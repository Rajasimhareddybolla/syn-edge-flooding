# Table T4: Ablation Analysis of D2 Detection Branches (Test Set)

| Branch Configuration                                     | Target Attack Modes                      | SYN Flood Det Rate   | Conn Flood Det Rate   | Mitigated Flood Det Rate   | Overall Test Recall   | False Alarm Rate   |
|:---------------------------------------------------------|:-----------------------------------------|:---------------------|:----------------------|:---------------------------|:----------------------|:-------------------|
| Branch 1 Alone (D1: Volume + HCR)                        | SYN Floods (S2L/M/H, S4)                 | 100.0% (8/8)         | 0.0% (0/6)            | 100.0% (4/4)               | 66.7% (12/18)         | 0.0% (0/8)         |
| Branch 1 + Branch 2 (+ESTAB / Source Concentration)      | SYN Floods + Connection Hold Floods (S3) | 100.0% (8/8)         | 100.0% (6/6)          | 100.0% (4/4)               | 100.0% (18/18)        | 12.5% (1/8)        |
| Branch 1 + Branch 2 + Branch 3 (Full D2 with Mitigation) | All Floods + SYN Cookie Defense Active   | 100.0% (8/8)         | 100.0% (6/6)          | 100.0% (4/4)               | 100.0% (18/18)        | 12.5% (1/8)        |
