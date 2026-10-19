from speak_gate import gate

MESSAGES = [
    "Bob: lol that meme was hilarious",
    "Priya: I'll send the budget report to finance by Friday.",
    "Alice: @Hush what time is the client call tomorrow?",
    "Sam: Anyone know where the Q3 slides are?",
    "Dev: Hush, note that Maria owns the demo.",
    "Lena: We need to ship by the 30th, no exceptions.",
    "Raj: Thanks everyone, great meeting!",
    "Mia: @Hush summarize what we decided so far",
]

for message in MESSAGES:
    d = gate(message)
    s = d.signals
    print(
        f"{d.action.value:6} | {message[:48]:48} | "
        f"a={s.get('addressed', 0):.2f} c={s.get('commitment', 0):.2f} "
        f"h={s.get('chitchat', 0):.2f} | {d.reason}"
    )