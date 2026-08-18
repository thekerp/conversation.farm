#!/usr/bin/env python3
"""Structural verification of beats.v1.json against segments.v1.jsonl.

Mechanical invariants only. Says nothing about whether a claim is FAIR to the
conversation -- that needs the adversarial semantic walk.

Quotes are matched on word sequence, not characters, so punctuation differences
do not create false positives. Two things are then reported separately:
  - quote-smoothed:  matched only after removing the speaker's disfluency
  - quote-truncated: the quote ends mid-sentence in the source but is closed
                     with a full stop, which is the documented blocking defect
                     class on this convo.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

CLAIM_LIMIT = 300
PAD = 0.25  # stage 7's mandated clip pad

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("convo_dir", type=Path, help="convos/<farm>-<n>/")
ap.add_argument("--json", type=Path, metavar="OUT",
                help="also write the findings as JSON to OUT")
args = ap.parse_args()

BASE = args.convo_dir.expanduser().resolve()
if not (BASE / "beats.v1.json").is_file():
    sys.exit(f"no beats.v1.json under {BASE}")

beats_doc = json.loads((BASE / "beats.v1.json").read_text(encoding="utf-8"))
segs = sorted((json.loads(l) for l in (BASE / "segments.v1.jsonl").open(encoding="utf-8")),
              key=lambda s: s["start"])
by_id = {s["id"]: s for s in segs}
cut_text = (BASE / "cut-material.v1.md").read_text(encoding="utf-8")

findings = []


def add(beat, sev, cat, msg):
    findings.append((beat, sev, cat, msg))


def fold(t):
    t = unicodedata.normalize("NFKC", t)
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
                 ("—", " "), ("–", " "), ("…", "..."), (" ", " ")]:
        t = t.replace(a, b)
    return t


STUTTER = re.compile(r"^[a-z]{1,3}$")


def tokens(t, drop_disfluency=False):
    """(word, char_offset) pairs. Apostrophes kept: don't != dont."""
    out = []
    for m in re.finditer(r"[a-z0-9']+", fold(t).lower()):
        w = m.group(0).strip("'")
        if not w:
            continue
        out.append((w, m.start()))
    if drop_disfluency:
        out = [(w, o) for w, o in out if w not in ("uh", "um", "er", "mm")]
    return out


def find_seq(hay, needle):
    """Index of contiguous needle in hay (lists of words), or -1."""
    if not needle or len(needle) > len(hay):
        return -1
    first = needle[0]
    for i in range(len(hay) - len(needle) + 1):
        if hay[i] == first and hay[i:i + len(needle)] == needle:
            return i
    return -1


class Source:
    def __init__(self, name, text):
        self.name = name
        self.text = fold(text)
        self.tok = tokens(self.text)
        self.words = [w for w, _ in self.tok]
        self.tok_nd = tokens(self.text, drop_disfluency=True)
        self.words_nd = [w for w, _ in self.tok_nd]


MASTER = Source("master", " ".join(s["text"] for s in segs))
CUT = Source("cut", cut_text)
SEG_SRC = {s["id"]: Source(s["id"], s["text"]) for s in segs}

SENT_END = re.compile(r"^\s*[.!?]")


def analyse_quote(q):
    """-> (where, smoothed, truncated_midsentence)"""
    frags = [f for f in (x.strip() for x in q.split("...")) if f]
    for src in (MASTER, CUT):
        pos, ok, last_end_char = 0, True, None
        for f in frags:
            need = [w for w, _ in tokens(f)]
            i = find_seq(src.words[pos:], need)
            if i < 0:
                ok = False
                break
            i += pos
            pos = i + len(need)
            last_tok = src.tok[pos - 1]
            last_end_char = last_tok[1] + len(last_tok[0])
        if ok:
            trailing = src.text[last_end_char:last_end_char + 3]
            closed_hard = q.rstrip().endswith((".", "!", "?"))
            mid = closed_hard and not SENT_END.match(trailing) and trailing.strip() != ""
            return src.name, False, mid
        # retry ignoring filler words
        pos, ok = 0, True
        for f in frags:
            need = [w for w, _ in tokens(f, drop_disfluency=True)]
            i = find_seq(src.words_nd[pos:], need)
            if i < 0:
                ok = False
                break
            pos = i + len(need)
        if ok:
            return src.name, True, False
    return None, False, False


def owning_segments(q):
    frags = [f for f in (x.strip() for x in q.split("...")) if f]
    hits = set()
    for sid, src in SEG_SRC.items():
        for f in frags:
            need = [w for w, _ in tokens(f)]
            if len(need) >= 5 and find_seq(src.words, need) >= 0:
                hits.add(sid)
    return hits


def quotes_in(text):
    parts = fold(text).split('"')
    return [p for i, p in enumerate(parts) if i % 2 == 1 and len(tokens(p)) >= 4]


beats = beats_doc["beats"]

for b in beats:
    bid, sids = b["id"], b.get("segment_ids", [])
    known = [by_id[s] for s in sids if s in by_id]

    if len(b["claim"]) > CLAIM_LIMIT:
        add(bid, "HIGH", "claim-length", f"claim is {len(b['claim'])} chars, limit {CLAIM_LIMIT}")
    if [s for s in sids if s not in by_id]:
        add(bid, "HIGH", "segment-missing", f"unknown segment_ids {[s for s in sids if s not in by_id]}")
    if not known:
        add(bid, "HIGH", "segment-missing", "resolves to zero real segments")
        continue
    if sids != sorted(sids):
        add(bid, "MED", "segment-order", "segment_ids not ascending")
    if b["speaker"] not in {s["speaker"] for s in known}:
        add(bid, "HIGH", "speaker-mismatch", f"'{b['speaker']}' in none of its segments")
    confs = {s.get("speaker_confidence") for s in known}
    if b.get("speaker_confidence") == "confirmed" and confs != {"confirmed"}:
        add(bid, "HIGH", "confidence-overstated", f"segments carry {sorted(c for c in confs if c)}")
    if [s["id"] for s in known if s.get("disputed")]:
        add(bid, "MED", "disputed-segment", f"{[s['id'] for s in known if s.get('disputed')]}")

    lo = min(s["start"] for s in known)
    hi = max(s["end"] for s in known)
    if b["t_end"] <= b["t"]:
        add(bid, "HIGH", "window", f"t_end {b['t_end']} <= t {b['t']}")
    if b["t"] < lo - 0.001:
        add(bid, "MED", "window", f"t={b['t']} precedes first cited segment start {lo}")
    if b["t_end"] > hi + 0.001:
        add(bid, "HIGH", "window-uncited",
            f"t_end={b['t_end']} runs {b['t_end']-hi:.2f}s past last cited segment "
            f"({max(known, key=lambda s: s['end'])['id']} ends {hi})")
    for s in segs:
        if s["start"] < b["t_end"] < s["end"] and s["id"] not in sids:
            add(bid, "HIGH", "mid-segment-cut",
                f"t_end={b['t_end']} falls inside {s['id']} ({s['speaker']}, {s['start']}-{s['end']}), "
                "not in segment_ids")
    nxt = next((s for s in segs if s["start"] > b["t_end"] + 1e-9), None)
    if nxt and nxt["start"] - b["t_end"] < PAD - 1e-9:
        add(bid, "HIGH", "pad-collision",
            f"{nxt['id']} starts {nxt['start']-b['t_end']:.3f}s after t_end; {PAD}s pad pulls in "
            f"'{nxt['speaker']}'")
    tei = b.get("t_end_intended")
    if tei is not None and tei < b["t_end"] - 0.001:
        add(bid, "MED", "intended-bound",
            f"t_end_intended {tei} is BEFORE snapped t_end {b['t_end']}; the snap ran forward, "
            "but snapping is documented as trimming back to a word end")

    for field in ("claim", "context"):
        for q in quotes_in(b.get(field, "")):
            where, smoothed, mid = analyse_quote(q)
            short = re.sub(r"\s+", " ", q)[:64]
            if where is None:
                add(bid, "HIGH", "quote-not-found", f'{field}: "{short}"')
                continue
            if smoothed:
                add(bid, "MED", "quote-smoothed", f'{field}: disfluency removed: "{short}"')
            if mid:
                add(bid, "MED", "quote-truncated",
                    f'{field}: closed with a full stop but the source sentence continues: "{short}"')
            if where == "cut" and "source_timeline_note" not in b:
                add(bid, "HIGH", "quote-from-cut", f'{field}: from cut material, no note: "{short}"')
            if where == "master":
                own = owning_segments(q)
                if own and not (own & set(sids)):
                    add(bid, "HIGH", "quote-uncited-segment",
                        f'{field}: lives in {sorted(own)}, not in segment_ids: "{short}"')

    for ts in re.findall(r"\((\d{3,4}\.\d+)\)", b.get("context", "")):
        t = float(ts)
        if not any(s["start"] - 0.05 <= t <= s["end"] + 0.05 for s in segs):
            add(bid, "MED", "timestamp", f"context cites {t}s, inside no segment")

if len({b["id"] for b in beats}) != len(beats):
    add("-", "HIGH", "duplicate-id", "duplicate beat ids")
for a, b in zip(beats, beats[1:]):
    if b["t"] < a["t_end"]:
        add(f"{a['id']}/{b['id']}", "HIGH", "overlap", f"{a['id']} ends {a['t_end']}, {b['id']} starts {b['t']}")
seen = set()
for b in beats:
    for s in b.get("segment_ids", []):
        if s in seen:
            add(b["id"], "MED", "segment-reuse", f"{s} cited by more than one beat")
        seen.add(s)

rank = {"HIGH": 0, "MED": 1, "LOW": 2}
findings.sort(key=lambda f: (rank[f[1]], f[0]))
print(f"{len(findings)} structural findings across {len(beats)} beats\n" if findings
      else f"PASS: no structural findings across {len(beats)} beats.")
for bid, sev, cat, msg in findings:
    print(f"[{sev:4}] {bid:9} {cat:21} {msg}")
n_hi = sum(1 for f in findings if f[1] == "HIGH")
n_med = sum(1 for f in findings if f[1] == "MED")
print(f"\nHIGH={n_hi} MED={n_med}")

if args.json:
    args.json.write_text(json.dumps({
        "convo": beats_doc.get("convo"),
        "stage": "3b",
        "checks": "structural only — says nothing about whether a claim is fair to the "
                  "conversation, which needs the adversarial semantic walk",
        "sources": ["beats.v1.json", "segments.v1.jsonl", "cut-material.v1.md"],
        "beats_checked": len(beats),
        "counts": {"HIGH": n_hi, "MED": n_med},
        "findings": [{"beat": b, "severity": s, "category": c, "detail": m}
                     for b, s, c, m in findings],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.json}")

sys.exit(1 if n_hi else 0)
