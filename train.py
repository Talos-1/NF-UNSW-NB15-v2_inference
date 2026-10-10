import json
import os

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import average_precision_score, classification_report
from sklearn.model_selection import train_test_split

nb15 = pd.read_csv("data/NF-UNSW-NB15-v2.csv")
nb15 = nb15.drop(columns=["IPV4_SRC_ADDR", "IPV4_DST_ADDR", "L4_SRC_PORT"])
feats = [c for c in nb15.columns if c not in ["Label", "Attack"]]
nb15 = nb15.drop_duplicates(subset = feats + ["Label"])

X = nb15[feats]
y = nb15["Label"]

x_train, x_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, stratify=nb15["Attack"], random_state=42)
x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, stratify=nb15.loc[x_temp.index, "Attack"], random_state=42)

booster = lgb.train({"objective": "binary", "verbose": -1}, lgb.Dataset(x_train, y_train))
raw_pred = booster.predict(x_val)
pred = (raw_pred >= 0.5).astype(int)

print(f"PR-AUC: {average_precision_score(y_val, raw_pred)}")
print(classification_report(y_val, pred, target_names=["Benign", "Attack"]))

attack_val = nb15.loc[x_val.index, "Attack"]
print(pd.crosstab(attack_val, pred, normalize="index")[1].sort_values())

os.makedirs('model', exist_ok=True)

booster.save_model("model/model.txt")
with open("model/model_meta.json", "w") as f:
    json.dump({"features": feats, "threshold": 0.5}, f, indent=2)

x_test.to_csv("data/test.csv", index_label="flow_id")

test_df = x_test.assign(Label=y_test, Attack=nb15.loc[x_test.index, "Attack"])
test_df.to_csv("data/test_full_dataset.csv", index_label="flow_id")