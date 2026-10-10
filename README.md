# NF-UNSW-NB15-v2_inference

A project running binary network intrusion detection on the NF-UNSW-NB-15-v2 dataset, using LightGBM, served on a FastAPI endpoint with batch inference.

The [NF-UNSW-NB15-v2](https://rdm.uq.edu.au/files/8c6e2a00-ef9c-11ed-827d-e762de186848) dataset contains 2,390,275 flows and 43 NetFlow features, covering 9 attack categories. The dataset should be downloaded and placed in `data/NF-UNSW-NB15-v2.csv`.

Hyperparameter optimisation was performed using `optuna`, with 40 variations tested. It turned out that similar results were achieved using the base model so this was kept for simplicity.

## Running the Project

```bash
cd NF-UNSW-NB15-v2_inference
poetry install
eval $(poetry env activate)

python train.py #train, evaluate on validation dataset, write model and save test split.
uvicorn server:app --port 8000 #start the inference server
python client.py # in a second terminal, score the test split.
```

## Results

```bash
$ python train.py
PR-AUC: 0.9667
              precision    recall  f1-score   support

      Benign       1.00      1.00      1.00    123184
      Attack       0.92      0.95      0.93      5935

    accuracy                           0.99    129119
   macro avg       0.96      0.97      0.97    129119
weighted avg       0.99      0.99      0.99    129119

Attack
Benign            0.003905
Analysis          0.203704
Fuzzers           0.832731
DoS               0.951883
Backdoor          0.967742
Exploits          0.980169
Generic           1.000000
Reconnaissance    1.000000
Shellcode         1.000000
Worms             1.000000
```

```bash
$ python client.py
{'status': 'ok'}
100%|██████████████████████████████████████| 13/13 [00:01<00:00,  6.78it/s]
Predicted:
Benign: 123050 (95.2997%)
Malicious: 6069 (4.7003%)

Total flows: 129119
Predicted in 1.92s
Saved to 'data/predictions.csv'
```
