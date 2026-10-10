import time

import pandas as pd
import requests
from tqdm import tqdm

URL = "http://localhost:8000"
BATCH_SIZE = 10_000

df = pd.read_csv("data/test.csv", index_col="flow_id")

print(requests.get(f"{URL}/health", timeout=10).json())

preds = []

time_start = time.time()

for start in tqdm(range(0, len(df), BATCH_SIZE)):
    batch = df.iloc[start:start+BATCH_SIZE]
    payload = {"columns": batch.columns.tolist(), "flows": batch.to_numpy().tolist()}
    r = requests.post(f"{URL}/predict", json=payload, timeout=60)
    if not r.ok:
        print(r.status_code, r.json()["detail"])
    r.raise_for_status()
    preds += r.json()["predictions"]

time_end = time.time()

output = pd.DataFrame(preds, index=df.index)
output.to_csv("data/predictions.csv")

total = len(output)
n_malicious = int(output["is_malicious"].sum())
n_benign = total - n_malicious
runtime = time_end - time_start

print("Predicted:")
print(f"Benign: {n_benign} ({round(n_benign / total * 100, 4)}%)")
print(f"Malicious: {n_malicious} ({round(n_malicious / total * 100, 4)}%)")
print()
print(f"Total flows: {total}")
print(f"Predicted in {round(runtime, 2)}s")
print("Saved to 'data/predictions.csv'")