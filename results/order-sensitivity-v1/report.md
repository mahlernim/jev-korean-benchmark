# Sentence-order sensitivity on PAWS-X

Reversing sentence1 and sentence2 leaves paraphrase equivalence unchanged, so a changed
prediction is an inconsistency. Both orientations were run inside this experiment.

| Model / condition | n | Flips | Flip rate (95% CI) | Mean prob. total variation |
|---|---:|---:|---:|---:|
| jev/en_en | 100 | 14 | 14% (9, 22) | 0.101 |
| jev/ko_ko | 100 | 13 | 13% (8, 21) | 0.117 |
| luna/en_en | 100 | 11 | 11% (6, 19) | — |
| luna/ko_ko | 100 | 21 | 21% (14, 30) | — |

| Model / condition | Accuracy original | Accuracy reversed |
|---|---:|---:|
| jev/en_en | 79/100 | 89/100 |
| jev/ko_ko | 75/100 | 74/100 |
| luna/en_en | 81/100 | 88/100 |
| luna/ko_ko | 74/100 | 73/100 |

| Model | Korean minus English flip rate, pp (95% paired interval) |
|---|---:|
| jev | -1 (-9, +7) |
| luna | +10 (-1, +20) |

Successful 800 of 800. Estimated cost $0.02177.

Luna returns a decision only, so no probability total variation is available for it.
