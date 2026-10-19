"""Hush: group-chat copilot. The Decider decides, Amazon Bedrock only writes replies.

    hush = Hush()
    reply = hush.handle("Alice: @Hush what did we decide about pricing?")
    # reply is a string when Hush speaks, None when it stays silent or takes a note.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from strands import Agent

from patterns.speak_or_stay_silent.handler import HushGate
from patterns.speak_or_stay_silent.speak_gate import Action, Decision, gate

# Copy the exact ID from the Bedrock console (Inference profiles) if this one is rejected.
DEFAULT_MODEL_ID = "global.amazon.nova-2-lite-v1:0"
DEFAULT_REGION = "us-east-1"

SYSTEM = (
    "You are Hush, a quiet meeting assistant. Answer the new message in at most two "
    "sentences, using only the meeting context below. If the context does not contain "
    "the answer, say you do not know.\n\n"
)


@dataclass
class Outcome:
    decision: Decision
    reply: str | None = None


def bedrock_model():
    from strands.models import BedrockModel

    return BedrockModel(
        model_id=os.environ.get("HUSH_MODEL_ID", DEFAULT_MODEL_ID),
        region_name=os.environ.get("AWS_REGION", DEFAULT_REGION),
    )


class Hush:
    def __init__(self, model=None, gate_fn=gate, keep: int = 30):
        self.model = model
        self.gate_fn = gate_fn
        self.keep = keep
        self.transcript: list[str] = []
        self.notes: list[str] = []
        self.llm_calls = 0

    def _context(self) -> str:
        notes = "\n".join(f"- {n}" for n in self.notes) or "(none)"
        recent = "\n".join(self.transcript[-self.keep:]) or "(empty)"
        return f"Action items noted so far:\n{notes}\n\nRecent messages:\n{recent}"

    def handle(self, message: str) -> Outcome:
        handler = HushGate(self.gate_fn)
        agent = Agent(
            model=self.model or bedrock_model(),
            system_prompt=SYSTEM + self._context(),
            interventions=[handler],
            callback_handler=None,
        )
        result = agent(message)
        decision = handler.last_decision
        if decision is None:  # handler failed and the agent stayed quiet
            decision = Decision(Action.SILENT, "gate error, stayed quiet")
        self.transcript.append(message)
        if decision.action == Action.NOTE:
            self.notes.append(message)
        if decision.action == Action.SPEAK:
            self.llm_calls += 1
            return Outcome(decision, str(result).strip())
        return Outcome(decision, None)
