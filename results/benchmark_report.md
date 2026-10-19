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

## Hard split (30 messages written to defeat keyword rules, same thresholds)

| method | accuracy | false interruptions | missed answers | missed notes |
|---|---|---|---|---|
| Decider + speak_gate (HI=0.50, LO=0.45) | 66.7% | 1 | 0 | 5 |
| Decider + speak_gate (fixed 0.65 / 0.35) | 60.0% | 1 | 2 | 6 |
| Keyword baseline (regex) | 36.7% | 7 | 0 | 5 |

Hard messages the tuned Decider got wrong:

- `Friday works for me, count me in for the slides.` gold=note got=silent (addressed 0.27, commitment 0.30, chitchat 0.41)
- `Consider it done, the contract is mine.` gold=note got=silent (addressed 0.22, commitment 0.36, chitchat 0.28)
- `Sure, I own the QA sign-off.` gold=note got=silent (addressed 0.33, commitment 0.21, chitchat 0.26)
- `Leave the vendor call to me, I'll handle it.` gold=note got=silent (addressed 0.44, commitment 0.23, chitchat 0.34)
- `Put me down for the demo setup.` gold=note got=silent (addressed 0.37, commitment 0.16, chitchat 0.35)
- `That deadline last quarter was ridiculous.` gold=silent got=note (addressed 0.25, commitment 0.73, chitchat 0.38)
- `Remember, the 2019 release was due by Friday and still slipped.` gold=silent got=note (addressed 0.24, commitment 0.65, chitchat 0.19)
- `Shh, hush everyone, the speaker is starting.` gold=silent got=speak (addressed 0.55, commitment 0.11, chitchat 0.39)
- `It would be nice to have the report by Friday.` gold=silent got=note (addressed 0.21, commitment 0.74, chitchat 0.19)
- `Honestly the Friday deadline stresses me out.` gold=silent got=note (addressed 0.24, commitment 0.88, chitchat 0.27)

## Latency (this machine, one call = three questions)

- server-side median 4811 ms, max 36406 ms
- end-to-end median 6852 ms, max 38620 ms
- Hardware: record it here (CPU or GPU model). The published ~115 ms figure is for an RTX 3090.

## Test messages the Decider got wrong

- `Zoe: The hush-hush project is almost done.` gold=silent got=note (addressed 0.31, commitment 0.61, chitchat 0.22)