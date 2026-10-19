"""Benchmark the speak_gate decision on the labeled dataset.

Step 1: ask the local Decider server for the three yes/no probabilities of every
        message (cached in results/decider_signals.jsonl, safe to stop and resume).
Step 2: tune the two thresholds on the DEV split only.
Step 3: report on the TEST split, next to a plain keyword baseline.

Usage:  python benchmark.py            (server must be running on port 8000)
        python benchmark.py --limit 6  (quick smoke test on the first 6 messages)
        python benchmark.py --offline  (skip the server, reuse the cache)
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
from collections import Counter
from pathlib import Path

from speak_gate import decide, ask_decider, Action

ROOT = Path(__file__).parent
DATA = ROOT / "data" / "messages.jsonl"
CACHE = ROOT / "results" / "decider_signals.jsonl"
REPORT = ROOT / "results" / "benchmark_report.md"
LABELS = ["speak", "note", "silent"]


def load_rows():
    return [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_cache():
    cache = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[r["id"]] = r
    return cache


def collect_signals(rows, limit=None):
    CACHE.parent.mkdir(exist_ok=True)
    cache = load_cache()
    todo = [r for r in rows[:limit] if r["id"] not in cache] if limit else [r for r in rows if r["id"] not in cache]
    if todo:
        print(f"asking the Decider about {len(todo)} messages ({len(cache)} already cached)")
    with CACHE.open("a", encoding="utf-8") as f:
        for n, r in enumerate(todo, 1):
            t0 = time.perf_counter()
            try:
                signals, server_ms = ask_decider(r["text"])
            except (urllib.error.URLError, TimeoutError) as exc:
                sys.exit(f"\nCannot reach the Decider server ({exc}). Is `strands-decider serve` still running?")
            wall_ms = (time.perf_counter() - t0) * 1000
            rec = {"id": r["id"], "signals": signals, "server_ms": server_ms, "wall_ms": round(wall_ms)}
            f.write(json.dumps(rec) + "\n")
            f.flush()
            cache[r["id"]] = rec
            print(f"  [{n}/{len(todo)}] {r['id']} {wall_ms/1000:.1f}s", flush=True)
    return cache


# ---------- baseline: what a few lines of regex would do ----------
COMMIT_RE = re.compile(
    r"\b(i'll|i will|i'm going to|i promise|will finish|deadline|must be|need to|needs to|have to|"
    r"by (monday|tuesday|wednesday|thursday|friday|noon|tomorrow|end of|the \d)|due )\b",
    re.I,
)


def keyword_action(text):
    if re.search(r"\bhush\b", text, re.I):
        return "speak"
    if COMMIT_RE.search(text):
        return "note"
    return "silent"


# ---------- metrics ----------
def metrics(gold, pred):
    n = len(gold)
    acc = sum(g == p for g, p in zip(gold, pred)) / n
    false_speak = sum(p == "speak" and g != "speak" for g, p in zip(gold, pred))
    missed_speak = sum(g == "speak" and p != "speak" for g, p in zip(gold, pred))
    missed_note = sum(g == "note" and p != "note" for g, p in zip(gold, pred))
    conf = Counter(zip(gold, pred))
    return {"n": n, "acc": acc, "false_speak": false_speak, "missed_speak": missed_speak,
            "missed_note": missed_note, "conf": conf}


def predict(rows, cache, hi, lo):
    return [decide(cache[r["id"]]["signals"], hi, lo).action.value for r in rows]


def tune(dev, cache):
    best = None
    for hi_i in range(50, 90, 5):
        for lo_i in range(20, 55, 5):
            hi, lo = hi_i / 100, lo_i / 100
            if lo >= hi:
                continue
            m = metrics([r["action"] for r in dev], predict(dev, cache, hi, lo))
            key = (m["acc"], -m["false_speak"], -(hi - lo))
            if best is None or key > best[0]:
                best = (key, hi, lo, m)
    return best[1], best[2], best[3]


def confusion_table(conf):
    lines = ["| gold \\ predicted | speak | note | silent |", "|---|---|---|---|"]
    for g in LABELS:
        lines.append(f"| {g} | " + " | ".join(str(conf.get((g, p), 0)) for p in LABELS) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    rows = load_rows()
    if args.offline:
        cache = load_cache()
    else:
        cache = collect_signals(rows, args.limit)
    rows = [r for r in rows if r["id"] in cache]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]
    if not dev or not test:
        sys.exit("Need both dev and test messages cached. Run without --limit first.")

    hi, lo, dev_m = tune(dev, cache)
    out = []
    out.append("# Hush benchmark\n")
    out.append(f"Messages: {len(dev)} dev + {len(test)} test. Gold labels are in data/build_dataset.py.\n")
    out.append(f"Thresholds tuned on dev only: **HI={hi:.2f}, LO={lo:.2f}** (dev accuracy {dev_m['acc']:.1%}).\n")

    gold = [r["action"] for r in test]
    results = {
        f"Decider + speak_gate (HI={hi:.2f}, LO={lo:.2f})": predict(test, cache, hi, lo),
        "Decider + speak_gate (fixed 0.65 / 0.35)": predict(test, cache, 0.65, 0.35),
        "Keyword baseline (regex)": [keyword_action(r["text"]) for r in test],
        "Always silent": ["silent"] * len(test),
    }
    out.append("## Test split\n")
    out.append("| method | accuracy | false interruptions | missed answers | missed notes |")
    out.append("|---|---|---|---|---|")
    first = None
    for name, pred in results.items():
        m = metrics(gold, pred)
        first = first or m
        out.append(f"| {name} | {m['acc']:.1%} | {m['false_speak']} | {m['missed_speak']} | {m['missed_note']} |")
    out.append("\nFalse interruption = Hush spoke when it should not have. Missed answer = Hush stayed quiet when asked.\n")
    out.append("### Confusion matrix (Decider, tuned thresholds)\n")
    out.append(confusion_table(first["conf"]))

    lat = [cache[r["id"]]["server_ms"] for r in rows if cache[r["id"]].get("server_ms")]
    wall = [cache[r["id"]]["wall_ms"] for r in rows]
    out.append("\n## Latency (this machine, one call = three questions)\n")
    if lat:
        out.append(f"- server-side median {statistics.median(lat):.0f} ms, max {max(lat):.0f} ms")
    out.append(f"- end-to-end median {statistics.median(wall):.0f} ms, max {max(wall):.0f} ms")
    out.append("- Hardware: record it here (CPU or GPU model). The published ~115 ms figure is for an RTX 3090.\n")

    out.append("## Test messages the Decider got wrong\n")
    pred = results[next(iter(results))]
    wrong = [(r, p) for r, p in zip(test, pred) if r["action"] != p]
    if not wrong:
        out.append("None.")
    for r, p in wrong:
        s = cache[r["id"]]["signals"]
        out.append(f"- `{r['text']}` gold={r['action']} got={p} "
                   f"(addressed {s['addressed']:.2f}, commitment {s['commitment']:.2f}, chitchat {s['chitchat']:.2f})")

    text = "\n".join(out)
    REPORT.write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"\nreport saved to {REPORT}")


if __name__ == "__main__":
    main()
