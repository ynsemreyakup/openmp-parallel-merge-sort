# Threshold Comparison Results

All configurations were run sequentially, not in parallel with another benchmark process. Each value is the median of 5 runs.

## 5,000,000 Integers

| Version | Threads | Time (s) | Speedup | Efficiency | Checksum | Sorted |
|---|---:|---:|---:|---:|---:|---|
| Threshold | 1 | 0.516 | 1.000 | 1.000 | 2499530084831184 | true |
| Threshold | 2 | 0.284 | 1.814 | 0.907 | 2499530084831184 | true |
| Threshold | 4 | 0.200 | 2.583 | 0.646 | 2499530084831184 | true |
| Threshold | 8 | 0.151 | 3.410 | 0.426 | 2499530084831184 | true |
| Threshold | 12 | 0.134 | 3.844 | 0.320 | 2499530084831184 | true |
| No Threshold | 1 | 0.599 | 1.000 | 1.000 | 2499530084831184 | true |
| No Threshold | 2 | 0.330 | 1.816 | 0.908 | 2499530084831184 | true |
| No Threshold | 4 | 0.233 | 2.575 | 0.644 | 2499530084831184 | true |
| No Threshold | 8 | 0.167 | 3.600 | 0.450 | 2499530084831184 | true |
| No Threshold | 12 | 0.150 | 4.009 | 0.334 | 2499530084831184 | true |

## 50,000,000 Integers

| Version | Threads | Time (s) | Speedup | Efficiency | Checksum | Sorted |
|---|---:|---:|---:|---:|---:|---|
| Threshold | 1 | 6.182 | 1.000 | 1.000 | 25003167213512715 | true |
| Threshold | 2 | 3.350 | 1.845 | 0.923 | 25003167213512715 | true |
| Threshold | 4 | 2.382 | 2.595 | 0.649 | 25003167213512715 | true |
| Threshold | 8 | 1.818 | 3.400 | 0.425 | 25003167213512715 | true |
| Threshold | 12 | 1.618 | 3.822 | 0.319 | 25003167213512715 | true |
| No Threshold | 1 | 7.002 | 1.000 | 1.000 | 25003167213512715 | true |
| No Threshold | 2 | 3.765 | 1.860 | 0.930 | 25003167213512715 | true |
| No Threshold | 4 | 2.616 | 2.677 | 0.669 | 25003167213512715 | true |
| No Threshold | 8 | 1.917 | 3.653 | 0.457 | 25003167213512715 | true |
| No Threshold | 12 | 1.699 | 4.120 | 0.343 | 25003167213512715 | true |
