"""speak_gate - decide whether an assistant should speak, take a note, or stay silent.

One call to Strands Decider 2B asks three yes/no questions about a chat message.
Plain code then turns the three probabilities into an action. When the signals
are unsure, the gate stays silent (fail quiet).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from enum import Enum

DECIDER_URL = "http://localhost:8000/v1/systemone"

# A probability above HI counts as yes, below LO as no, in between as unsure.
HI = 0.65
LO = 0.35

QUESTIONS = {
    "addressed": {
        "type": "noul",
        "instructions": "Is this message directly addressed to the assistant named Hush?",
    },
    "commitment": {
        "type": "noul",
        "instructions": "Does this message contain a commitment to do a task or a deadline?",
    },
    "chitchat": {
        "type": "noul",
        "instructions": "Is this message only social chatter with no work content?",
    },
}


class Action(str, Enum):
    SPEAK = "speak"
    NOTE = "note"
    SILENT = "silent"


@dataclass
class Decision:
    action: Action
    reason: str
    signals: dict = field(default_factory=dict)
    latency_ms: float | None = None


def decide(signals: dict, hi: float = HI, lo: float = LO) -> Decision:
    """Pure code: turn the three yes-probabilities into an action."""
    a = signals["addressed"]
    c = signals["commitment"]
    h = signals["chitchat"]

    if a >= hi:
        if h >= hi:
            return Decision(Action.SILENT, "addressed but only chatter", signals)
        return Decision(Action.SPEAK, "addressed to the assistant", signals)
    if a > lo:
        return Decision(Action.SILENT, "unsure if addressed, stay quiet", signals)
    if c >= hi:
        return Decision(Action.NOTE, "commitment or deadline detected", signals)
    if c > lo:
        return Decision(Action.SILENT, "unsure about commitment, stay quiet", signals)
    return Decision(Action.SILENT, "nothing to do", signals)


def ask_decider(state: str, url: str = DECIDER_URL, timeout: float = 120.0):
    """One HTTP call to the Decider server. Returns (signals, latency_ms)."""
    body = json.dumps({"state": state, "questions": QUESTIONS}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.load(resp)
    signals = {name: out["answers"][name]["noul"] for name in QUESTIONS}
    return signals, out.get("latency_ms")


def gate(state: str, url: str = DECIDER_URL) -> Decision:
    """Ask the Decider, then decide. If the Decider is unreachable, stay silent."""
    try:
        signals, latency = ask_decider(state, url)
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        return Decision(Action.SILENT, f"decider unavailable ({type(exc).__name__}), stay quiet")
    decision = decide(signals)
    decision.latency_ms = latency
    return decision