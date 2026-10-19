"""Scripted meeting for the demo video: Hush listens, notes, and speaks only when addressed.

Needs: Decider server running on :8000 and working Bedrock access (see README).
    python run_meeting.py
"""
from hush_agent import Hush

MEETING = [
    "Bob: lol that meme was hilarious",
    "Priya: I'll send the budget report to finance by Friday.",
    "Sam: Anyone know where the Q3 slides are?",
    "Lena: We need to ship by the 30th, no exceptions.",
    "Alice: @Hush what did we decide about the shipping date?",
    "Raj: Thanks everyone, great meeting!",
    "Mia: @Hush list the action items so far",
]


def main():
    hush = Hush()
    for message in MEETING:
        out = hush.handle(message)
        tag = out.decision.action.value.upper()
        print(f"[{tag:6}] {message}")
        if out.reply:
            print(f"         Hush: {out.reply}")
    print(f"\n{len(MEETING)} messages, {hush.llm_calls} model calls, {len(hush.notes)} notes.")


if __name__ == "__main__":
    main()
