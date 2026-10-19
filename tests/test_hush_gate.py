"""Offline test: HushGate + Hush with a stub model and fake Decider signals.
Run from the repo root:  python -m tests.test_hush_gate
Needs strands-agents installed, no AWS and no Decider server.
"""
from strands.models import Model

from hush_agent import Hush
from patterns.speak_or_stay_silent.speak_gate import Action, decide

SIGNALS = {
    "Bob: lol that meme was hilarious": dict(addressed=0.1, commitment=0.1, chitchat=0.8),
    "Priya: I'll send the report by Friday.": dict(addressed=0.1, commitment=0.9, chitchat=0.1),
    "Alice: @Hush what is the deadline?": dict(addressed=0.8, commitment=0.2, chitchat=0.2),
    "Sam: Anyone seen the slides?": dict(addressed=0.2, commitment=0.1, chitchat=0.3),
}


def fake_gate(text):
    return decide(SIGNALS[text])


class StubModel(Model):
    def __init__(self):
        self.calls = 0

    def update_config(self, **kw):
        pass

    def get_config(self):
        return {}

    async def structured_output(self, output_model, prompt, system_prompt=None, **kw):
        raise NotImplementedError
        yield

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kw):
        self.calls += 1
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {}}}
        yield {"contentBlockDelta": {"delta": {"text": "Stub reply."}}}
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}
        yield {"metadata": {"usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                            "metrics": {"latencyMs": 1}}}


def main():
    model = StubModel()
    hush = Hush(model=model, gate_fn=fake_gate)
    got = {m: hush.handle(m) for m in SIGNALS}
    assert got["Bob: lol that meme was hilarious"].decision.action == Action.SILENT
    assert got["Priya: I'll send the report by Friday."].decision.action == Action.NOTE
    assert got["Alice: @Hush what is the deadline?"].decision.action == Action.SPEAK
    assert got["Alice: @Hush what is the deadline?"].reply == "Stub reply."
    assert got["Sam: Anyone seen the slides?"].reply is None
    assert model.calls == 1, f"model should be called once, was {model.calls}"
    assert hush.notes == ["Priya: I'll send the report by Friday."]
    assert hush.llm_calls == 1

    def broken_gate(text):
        raise RuntimeError("decider down")

    quiet = Hush(model=StubModel(), gate_fn=broken_gate)
    out = quiet.handle("Alice: @Hush hi")
    assert out.reply is None and quiet.model.calls == 0
    print("all tests passed: model called", model.calls, "time out of", len(SIGNALS), "messages")


if __name__ == "__main__":
    main()
