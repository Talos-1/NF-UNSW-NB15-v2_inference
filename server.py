import json
from contextlib import asynccontextmanager

import lightgbm as lgb
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

MODEL_PATH = "model/model.txt"
META_PATH = "model/model_meta.json"
state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"] = lgb.Booster(model_file=MODEL_PATH)
    with open(META_PATH) as f:
        data = json.load(f)
    state["features"] = data["features"]
    state["threshold"] = data["threshold"]
    yield
    state.clear()

app = FastAPI(lifespan=lifespan)

class Prediction(BaseModel):
    probability: float
    is_malicious: bool

class PredictRequest(BaseModel):
    columns: list[str]
    flows: list[list[float]] = Field(min_length = 1, max_length = 10_000)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def check_row_widths(self):
        n = len(self.columns)
        if any(len(row) != n for row in self.flows):
            raise ValueError("every row must have one value per column.")
        return self

class PredictResponse(BaseModel):
    threshold: float
    predictions: list[Prediction]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse, 
responses={400: {"description": "Missing features or missing feature values."}})
def predict(request: PredictRequest):
    features = state["features"]
    df = pd.DataFrame(request.flows, columns=request.columns)
    missing_cols = [f for f in features if f not in df.columns]

    if missing_cols:
        raise HTTPException(status_code=400, detail=f"Features missing: {missing_cols}")
    if df[features].isna().to_numpy().any():
        raise HTTPException(status_code=400, detail="Some flows have missing feature values.")

    probs = state["model"].predict(df[features])
    threshold = request.threshold if request.threshold is not None else state["threshold"]

    return PredictResponse(
        threshold=threshold,
        predictions=[
            Prediction(probability=round(float(p), 6), is_malicious=bool(p >= threshold)) for p in probs
            ],
    )