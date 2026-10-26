# Table T2: Detector Benchmark Summary on Held-Out Test Set (Reps 4–5)

| Detector                       | Detection Rate (%)   | False Alarm Rate (%)   | Median Delay (s)   | Mean Delay (s)   |   Precision |   Recall |   F1-Score |   AUC-ROC |
|:-------------------------------|:---------------------|:-----------------------|:-------------------|:-----------------|------------:|---------:|-----------:|----------:|
| B1 (Static Volume Threshold)   | 66.7%                | 0.0%                   | 1.15s              | 1.24s            |      0.3343 |   0.6446 |     0.4402 |    0.7751 |
| D1 (Adaptive Dual-Signal EWMA) | 66.7%                | 0.0%                   | 1.17s              | 1.41s            |      0.33   |   0.6411 |     0.4357 |    0.7635 |
| D2 (Extended Multi-Branch)     | 100.0%               | 12.5%                  | 1.19s              | 1.49s            |      0.4133 |   0.9571 |     0.5773 |    0.9331 |

*Note: Tuning strictly on Repetitions 1–3 (N=39); Evaluation strictly on Repetitions 4–5 (N=26).*
