# Hush benchmark

Messages: 60 dev + 60 test. Gold labels are in data/build_dataset.py.

Thresholds tuned on dev only: **HI=0.50, LO=0.45** (dev accuracy 96.7%).

## Test split

| method | accuracy | false interruptions | missed answers | missed notes |
|---|---|---|---|---|
| Decider + speak_gate (HI=0.50, LO=0.45) | 98.3% | 0 | 0 | 0 |
| Decider + speak_gate (fixed 0.65 / 0.35) | 85.0% | 2 | 6 | 1 |
| Keyword baseline (regex) | 90.0% | 5 | 0 | 1 |
| Always silent | 50.0% | 0 | 15 | 15 |

False interruption = Hush spoke when it should not have. Missed answer = Hush stayed quiet when asked.

### Confusion matrix (Decider, tuned thresholds)

| gold \ predicted | speak | note | silent |
|---|---|---|---|
| speak | 15 | 0 | 0 |
| note | 0 | 15 | 0 |
| silent | 0 | 1 | 29 |

## Latency (this machine, one call = three questions)

- server-side median 4835 ms, max 36406 ms
- end-to-end median 6868 ms, max 38620 ms
- Hardware: record it here (CPU or GPU model). The published ~115 ms figure is for an RTX 3090.

## Test messages the Decider got wrong

- `Zoe: The hush-hush project is almost done.` gold=silent got=note (addressed 0.31, commitment 0.61, chitchat 0.22)