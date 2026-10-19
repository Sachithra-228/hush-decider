# Pattern: speak-or-stay-silent gate  (`#policy`)

Decide, before any LLM call, whether an agent should **speak**, **take a note**, or **stay silent**
about an incoming chat message. Reusable for meeting copilots, support-channel bots, Slack/Discord
assistants, and any agent that listens to a stream it should not answer every time.

## What is in the pattern

| piece | file | what it is |
|---|---|---|
| Typed questions | `speak_gate.py` -> `QUESTIONS` | three yes/no (`noul`) questions: addressed to the assistant? commitment or deadline? only chatter? |
| Decision code | `speak_gate.py` -> `decide()` | maps three probabilities to `speak` / `note` / `silent` with two thresholds (`HI`, `LO`); the band between them is "unsure" and stays silent |
| Agent wiring | `handler.py` -> `HushGate` | a Strands `InterventionHandler` on `before_invocation`: `Proceed` only for `speak`, `Deny` otherwise, so no model call is made. `on_error = "deny"` makes failures stay quiet |

## How to use it

```python
from strands import Agent
from patterns.speak_or_stay_silent.handler import HushGate

handler = HushGate()                       # talks to a local Decider server on :8000
agent = Agent(model=my_model, interventions=[handler], callback_handler=None)
result = agent("Alice: @Hush what time is the client call?")
handler.last_decision                      # action, reason, the three probabilities
```

1. `pip install strands-decider strands-agents` and run
   `strands-decider serve StrandsAgents/strands-decider-2B-hobson-v21 --port 8000`.
2. Change the wording in `QUESTIONS` (for example the assistant's name) and re-tune `HI`/`LO` on a few dozen
   labeled messages of your own (`benchmark.py` shows how).
3. A denied invocation adds one short assistant message to the agent's history. Use a fresh `Agent` per
   incoming message and keep the conversation in the system prompt (see `hush_agent.py`).

## What we learned (see `results/benchmark_report.md` for the numbers)

- Three yes/no questions worked better than one 3-way choice. The 3-way choice was unsure (confidence
  0.18) on a message that plainly addressed the assistant; the yes/no question on the same message was decisive.
- Thresholds matter: our tuned band (0.50/0.45) beat the first guess (0.65/0.35), but it is narrow, so
  "stay silent when unsure" covers only a small band. Tune on your own data.
- Offline test with a stub model: `python -m tests.test_hush_gate`.
