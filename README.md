# Hush: a group-chat copilot that knows when to stay silent

Hush listens to a meeting or group chat. For every message, a small decision model
([Strands Decider 2B](https://github.com/strands-labs/strands-decider)) answers three yes/no questions
in one call, and plain code turns the answers into one of three actions:

| action | when | LLM call? |
|---|---|---|
| **speak** | the message is addressed to Hush | yes, Amazon Bedrock writes the reply |
| **note** | someone commits to a task or states a deadline | no |
| **silent** | everything else, or the signals are unsure | no |

When the Decider is unsure, or the server is unreachable, Hush stays quiet (fail quiet).

Decision pattern: `#policy` (classify an incoming message before the agent acts).

> Status: work in progress for the Agent Experience Hackathon. Simulation only, no real chat is read.

## The reusable pattern: speak-or-stay-silent gate

- Typed questions: three `noul` (yes/no) questions in `speak_gate.py` (`QUESTIONS`).
- Decision code: `decide()` maps the three probabilities to speak / note / silent with two thresholds.
- Wiring: `gate(message)` is one function call; the Strands `InterventionHandler` wiring is coming next.

Why three yes/no questions and not one 3-way choice: on our first test the 3-way choice was unsure on a
message that clearly addressed the assistant (confidence 0.18), while the yes/no question on the same
message was decisive (0.83). Question design changed the result.

## Run it

```
pip install strands-decider strands-agents boto3
strands-decider serve StrandsAgents/strands-decider-2B-hobson-v21 --port 8000
python demo.py
python benchmark.py
```

## Benchmark

`data/messages.jsonl` holds 120 labeled messages (60 dev, 60 test). Thresholds are tuned on dev only;
numbers are reported on test, next to a keyword baseline and an always-silent baseline.
Results are written to `results/benchmark_report.md`.

## License

MIT
