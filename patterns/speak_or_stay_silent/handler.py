"""HushGate: a Strands InterventionHandler that puts the speak-or-stay-silent decision
in front of the agent's model call.

Only a `speak` decision lets the agent run (and call the generative model). `note` and
`silent` stop the invocation before any LLM call is made. If the Decider fails or this
handler raises, `on_error = "deny"` makes the agent stay quiet (fail quiet).

Note: a denied invocation appends one short assistant message to the agent's history,
so use a fresh Agent per incoming message (see hush_agent.py) and put the meeting
context in the system prompt.
"""
from __future__ import annotations

from typing import Callable

from strands.interventions import Deny, InterventionHandler, Proceed

from .speak_gate import Action, Decision, gate


def last_user_text(messages) -> str:
    """Text of the newest user message in a Strands `messages` list."""
    for message in reversed(messages or []):
        if message.get("role") == "user":
            parts = [b["text"] for b in message.get("content", []) if "text" in b]
            if parts:
                return " ".join(parts)
    return ""


class HushGate(InterventionHandler):
    name = "hush-gate"

    def __init__(self, gate_fn: Callable[[str], Decision] = gate):
        self.gate_fn = gate_fn
        self.last_decision: Decision | None = None

    @property
    def on_error(self):
        return "deny"  # fail closed = stay silent

    def before_invocation(self, event, **kwargs):
        decision = self.gate_fn(last_user_text(event.messages))
        self.last_decision = decision
        if decision.action == Action.SPEAK:
            return Proceed(reason=decision.reason)
        return Deny(reason=f"{decision.action.value}: {decision.reason}")
