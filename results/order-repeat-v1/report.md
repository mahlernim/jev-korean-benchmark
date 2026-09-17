# Repeat-condition control

The same requests were sent a second time without any change. This separates ordinary
service nondeterminism from the effect of reversing sentence order.

| Jev condition | n | Same input, flip rate | Reversed order, flip rate |
|---|---:|---:|---:|
| en_en | 100 | 2% (1, 7) | 14% (9, 22) |
| ko_ko | 100 | 1% (0, 5) | 13% (8, 21) |

| Jev condition | Mean probability total variation, same input | Reversed order |
|---|---:|---:|
| en_en | 0.012 | 0.101 |
| ko_ko | 0.011 | 0.117 |

Successful 200 of 200. Estimated cost $0.00320.

Both columns use the same 100 source questions per condition. The repeat column is
a floor for the reversal column: any flip that a repeated identical request produces
is not attributable to sentence order.
