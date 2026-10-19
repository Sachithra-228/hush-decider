"""Build data/messages.jsonl, a labeled benchmark of group-chat messages for Hush.

Each row: (text, addressed, commitment, chitchat).
  addressed  - the message is directed at the assistant named Hush
  commitment - someone commits to a task or states a deadline
  chitchat   - only social talk, nothing to act on
The gold action is derived from the labels with the same policy Hush uses:
  addressed and not chitchat -> speak
  else commitment            -> note
  else                       -> silent
Thresholds are tuned on the dev split only; the test split is for the final numbers.
"""
import json
import pathlib
from collections import Counter

DEV = [
    # speak
    ("Alice: @Hush what time is the client call tomorrow?", 1, 0, 0),
    ("Mia: @Hush summarize what we decided so far", 1, 0, 0),
    ("Dev: Hush, note that Maria owns the demo.", 1, 1, 0),
    ("Tom: Hey Hush, can you list the open action items?", 1, 0, 0),
    ("Nina: @Hush who is presenting the roadmap on Thursday?", 1, 0, 0),
    ("Carlos: Hush, what did Priya say about the budget earlier?", 1, 0, 0),
    ("Zoe: @Hush please remind us when the sprint review starts.", 1, 0, 0),
    ("Ken: Hush, how many people confirmed for the offsite?", 1, 0, 0),
    ("Ana: @Hush draft a short recap of today's meeting.", 1, 0, 0),
    ("Omar: Hush can you check if we already discussed pricing?", 1, 0, 0),
    ("Lily: @Hush what's the deadline for the design handoff?", 1, 0, 0),
    ("Ben: Hush, is the Q3 report finished?", 1, 0, 0),
    ("Sara: @Hush explain that last message in simple words.", 1, 0, 0),
    ("Jon: Hey @Hush, what were the three blockers again?", 1, 0, 0),
    ("Rita: Hush, add Friday's standup to the notes please.", 1, 1, 0),
    # note
    ("Priya: I'll send the budget report to finance by Friday.", 0, 1, 0),
    ("Lena: We need to ship by the 30th, no exceptions.", 0, 1, 0),
    ("Marcus: I'll book the conference room for Monday.", 0, 1, 0),
    ("Yuki: I can take the onboarding doc, will finish it by Wednesday.", 0, 1, 0),
    ("Fatima: Let's make sure the contract is signed by end of week.", 0, 1, 0),
    ("Greg: I'll follow up with the vendor tomorrow morning.", 0, 1, 0),
    ("Hannah: Deadline for the slides is Thursday 5pm.", 0, 1, 0),
    ("Ivan: I'll review Sam's pull request tonight.", 0, 1, 0),
    ("Chloe: I promise to have the test plan ready before the demo.", 0, 1, 0),
    ("Raj: I'm going to fix the login bug by tomorrow.", 0, 1, 0),
    ("Elena: The invoice needs to go out by the 15th.", 0, 1, 0),
    ("Paul: I'll set up the staging server this afternoon.", 0, 1, 0),
    ("Mei: We'll deliver the prototype to the client on Tuesday.", 0, 1, 0),
    ("Luis: I'll write the release notes before we deploy.", 0, 1, 0),
    ("Dana: I'll email the agenda by noon.", 0, 1, 0),
    # silent: chitchat
    ("Bob: lol that meme was hilarious", 0, 0, 1),
    ("Raj: Thanks everyone, great meeting!", 0, 0, 1),
    ("Amy: Good morning all!", 0, 0, 1),
    ("Sue: haha same here", 0, 0, 1),
    ("Tim: Happy birthday Jess!", 0, 0, 1),
    ("Nora: Nice weather today, finally some sun.", 0, 0, 1),
    ("Kyle: brb, coffee", 0, 0, 1),
    ("Pam: That lunch was amazing.", 0, 0, 1),
    ("Joe: lol yes", 0, 0, 1),
    ("Ivy: Have a good weekend, everyone!", 0, 0, 1),
    # silent: questions for other people
    ("Sam: Anyone know where the Q3 slides are?", 0, 0, 0),
    ("Alex: Does anyone have the Wi-Fi password?", 0, 0, 0),
    ("Rob: Priya, did you get a chance to look at the mockups?", 0, 0, 0),
    ("Gina: Who's joining the 3pm call?", 0, 0, 0),
    ("Hal: Is the printer on the second floor working?", 0, 0, 0),
    ("Vera: Dev, can you share your screen?", 0, 0, 0),
    # silent: work talk without a commitment
    ("Max: The server logs look fine from my side.", 0, 0, 0),
    ("Cleo: I think the design is a bit too busy.", 0, 0, 0),
    ("Dan: The client seemed happy with the demo.", 0, 0, 0),
    ("Fay: Our traffic doubled last week.", 0, 0, 0),
    ("Gus: That approach could work.", 0, 0, 0),
    ("Isla: I read the spec, it's long.", 0, 0, 0),
    # silent: tricky
    ("Ned: Everyone hush for a second, the CEO is joining.", 0, 0, 0),
    ("Opal: Can we keep this hush-hush until the announcement?", 0, 0, 0),
    ("Pete: Hush was a good name for the project, honestly.", 0, 0, 0),
    ("Quin: @Sam what's the status of the migration?", 0, 0, 0),
    ("Rosa: Thanks Hush!", 1, 0, 1),
    ("Stan: Hush, thanks, that's all.", 1, 0, 1),
    ("Tess: Maybe we could think about it next quarter.", 0, 0, 0),
    ("Uma: If we have time, I might look at the bug.", 0, 0, 0),
]

TEST = [
    # speak
    ("Wes: @Hush when is the next board meeting?", 1, 0, 0),
    ("Xena: Hush, give me a quick summary of the last ten minutes.", 1, 0, 0),
    ("Yara: @Hush what did we agree on for the launch date?", 1, 0, 0),
    ("Zack: Hush, please note that I'm taking the API docs.", 1, 1, 0),
    ("Abe: Hey Hush, who owns the payment integration?", 1, 0, 0),
    ("Bea: @Hush list everything assigned to Marcus.", 1, 0, 0),
    ("Cam: Hush, what's on the agenda for tomorrow?", 1, 0, 0),
    ("Dora: @Hush can you remind me what the budget cap was?", 1, 0, 0),
    ("Eli: Hush, record that the review moved to Friday.", 1, 1, 0),
    ("Flo: @Hush has anyone mentioned the security audit?", 1, 0, 0),
    ("Gil: Hush, what are the next steps?", 1, 0, 0),
    ("Hope: @Hush explain what 'blocked' means in our tracker.", 1, 0, 0),
    ("Ian: Hush, how long did the demo run?", 1, 0, 0),
    ("Jade: @Hush tell us the top two risks we raised.", 1, 0, 0),
    ("Kai: Hush, can you pull up last week's decisions?", 1, 0, 0),
    # note
    ("Leo: I'll deploy the hotfix before 6pm.", 0, 1, 0),
    ("Maya: The beta must be live by November 1st.", 0, 1, 0),
    ("Nick: I will draft the press release by Thursday.", 0, 1, 0),
    ("Olga: I'll sync with the design team tomorrow and report back.", 0, 1, 0),
    ("Quincy: I'm taking ownership of the migration plan, due next Monday.", 0, 1, 0),
    ("Ruth: We have to submit the grant application by the 25th.", 0, 1, 0),
    ("Seth: I'll pay the vendor invoice this week.", 0, 1, 0),
    ("Tara: I'll run the load tests tonight.", 0, 1, 0),
    ("Umar: I'll get approval from legal by Wednesday.", 0, 1, 0),
    ("Vic: Let's lock the scope by Friday, no more changes after that.", 0, 1, 0),
    ("Wendy: I'll prepare the demo environment before the call.", 0, 1, 0),
    ("Xavi: I'll update the roadmap by end of day.", 0, 1, 0),
    ("Yvonne: I will send the survey results on Monday.", 0, 1, 0),
    ("Zane: I'll fix the typo in the docs today.", 0, 1, 0),
    ("Amir: Our delivery date to the customer is the 12th.", 0, 1, 0),
    # silent: chitchat
    ("Beth: Haha that gif is perfect", 0, 0, 1),
    ("Carl: Morning folks!", 0, 0, 1),
    ("Didi: Thanks all, see you tomorrow!", 0, 0, 1),
    ("Erin: ok cool", 0, 0, 1),
    ("Finn: Congrats on the promotion, Tom!", 0, 0, 1),
    ("Gwen: The rain is crazy today.", 0, 0, 1),
    ("Hugo: Lunch was great, I'm already full.", 0, 0, 1),
    ("Iris: That was a fun retro.", 0, 0, 1),
    ("Jake: lol", 0, 0, 1),
    ("Kate: Enjoy your vacation, Paul!", 0, 0, 1),
    # silent: questions for other people
    ("Liam: Does anyone know who set up the shared drive?", 0, 0, 0),
    ("Mona: Chris, are you free to pair on this later?", 0, 0, 0),
    ("Nate: What time does the office close on Friday?", 0, 0, 0),
    ("Opie: Has the build finished yet?", 0, 0, 0),
    ("Pia: Anyone seen the HDMI cable?", 0, 0, 0),
    ("Rex: Jess, did the client reply to your email?", 0, 0, 0),
    # silent: work talk without a commitment
    ("Sid: The latency looks higher than last week.", 0, 0, 0),
    ("Tina: I don't love the new logo.", 0, 0, 0),
    ("Uri: The team seemed tired after the release.", 0, 0, 0),
    ("Val: That bug is annoying.", 0, 0, 0),
    ("Walt: The proposal reads well.", 0, 0, 0),
    ("Xia: Nothing new from the vendor yet.", 0, 0, 0),
    # silent: tricky
    ("Yan: Can everyone hush, I can't hear Anna.", 0, 0, 0),
    ("Zoe: The hush-hush project is almost done.", 0, 0, 0),
    ("Adam: Hush is a funny name for a bot.", 0, 0, 0),
    ("Bree: @Dev can you take a look at the failing test?", 0, 0, 0),
    ("Cody: Thanks Hush, that helped!", 1, 0, 1),
    ("Dina: Hush, never mind.", 1, 0, 1),
    ("Evan: Maybe we should consider moving the launch someday.", 0, 0, 0),
    ("Fern: I might possibly have time to look at it next week.", 0, 0, 0),
]

# Hard split: written to defeat keyword rules (implicit commitments, "hush" used as a
# normal word, "I'll"/"need to"/"deadline" without a real commitment, odd casing).
HARD = [
    ("Quick one for you, Hush: what's the refund policy?", 1, 0, 0),
    ("Could you recap the decisions, Hush?", 1, 0, 0),
    ("hush, what time does the demo start", 1, 0, 0),
    ("Before we move on, Hush, did we agree on the budget?", 1, 0, 0),
    ("HUSH what are today's action items", 1, 0, 0),
    ("Okay Hush, remind us who volunteered for the demo.", 1, 0, 0),
    ("Friday works for me, count me in for the slides.", 0, 1, 0),
    ("Consider it done, the contract is mine.", 0, 1, 0),
    ("Sure, I own the QA sign-off.", 0, 1, 0),
    ("Leave the vendor call to me, I'll handle it.", 0, 1, 0),
    ("I can have the draft in your inbox before lunch tomorrow.", 0, 1, 0),
    ("Put me down for the demo setup.", 0, 1, 0),
    ("The audit report is due the 28th, no extensions.", 0, 1, 0),
    ("I'll be honest, that idea is terrible.", 0, 0, 0),
    ("We need to talk about how loud the office is, lol", 0, 0, 1),
    ("That deadline last quarter was ridiculous.", 0, 0, 0),
    ("I will never understand this tracker.", 0, 0, 0),
    ("Remember, the 2019 release was due by Friday and still slipped.", 0, 0, 0),
    ("Shh, hush everyone, the speaker is starting.", 0, 0, 0),
    ("My daughter says hush whenever I sing.", 0, 0, 0),
    ("Hush puppies are the best part of the menu.", 0, 0, 0),
    ("Hush, you're hilarious lol", 1, 0, 1),
    ("Anyone know who's covering the on-call this weekend?", 0, 0, 0),
    ("Thanks Hush, great recap earlier!", 1, 0, 1),
    ("Maria, can you handle the invoice? Hush is busy with notes.", 0, 0, 0),
    ("I might be able to help next week, not sure yet.", 0, 0, 0),
    ("It would be nice to have the report by Friday.", 0, 0, 0),
    ("Honestly the Friday deadline stresses me out.", 0, 0, 0),
    ("Great point, Dana, I agree.", 0, 0, 1),
    ("lol we should totally ask Hush to write our emails", 0, 0, 0),
]


def gold_action(addressed, commitment, chitchat):
    if addressed and not chitchat:
        return "speak"
    if commitment:
        return "note"
    return "silent"


def main():
    rows = []
    for split, items in (("dev", DEV), ("test", TEST), ("hard", HARD)):
        for i, (text, a, c, h) in enumerate(items, 1):
            rows.append(
                {
                    "id": f"{split}-{i:02d}",
                    "split": split,
                    "text": text,
                    "addressed": a,
                    "commitment": c,
                    "chitchat": h,
                    "action": gold_action(a, c, h),
                }
            )
    out = pathlib.Path(__file__).with_name("messages.jsonl")
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {out}")
    for split in ("dev", "test", "hard"):
        print(split, dict(Counter(r["action"] for r in rows if r["split"] == split)))


if __name__ == "__main__":
    main()
