#!/usr/bin/env python3
"""Structural verification of research-queue.v1.json before stage 4b spends money.

Stage 4b is the expensive half of the research pass: one deep-research job per
question, real minutes and real dollars. This checks the queue is worth running
BEFORE a human is asked to approve it at Gate 1.

Mechanical invariants only. It cannot tell you whether a question is a good
question -- that is what the human gate is for. What it can tell you:

  - an anchor that addresses the wrong moment, which is the documented failure
    mode on this convo (the cold open was lifted from 20:41 and MOVED, so a
    master timestamp of 0 quotes audio from twenty minutes in)
  - a `verify` aimed at something the speaker never asserted, which anti-slop
    rule 7 forbids
  - a `since` on a convo old enough to need one, missing
  - budget, coverage and duplicate drift
"""
import argparse
import json
import re
import sys
from pathlib import Path

QUEUE_MIN, QUEUE_MAX = 6, 12  # docs/research-pass.md §6
TYPES = {"identify", "enrich", "verify", "contradict", "since"}
FEEDS = {"tendril", "check", "check+tendril"}
MAX_TENDRILS_PER_BEAT = 3  # §3 rule 3
SINCE_AGE_YEARS = 3

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("convo_dir", type=Path, help="convos/<farm>-<n>/")
ap.add_argument("--json", type=Path, metavar="OUT",
                help="also write the findings as JSON to OUT")
args = ap.parse_args()

BASE = args.convo_dir.expanduser().resolve()
qpath = BASE / "research-queue.v1.json"
if not qpath.is_file():
    sys.exit(f"no research-queue.v1.json under {BASE}")

qdoc = json.loads(qpath.read_text(encoding="utf-8"))
beats_doc = json.loads((BASE / "beats.v1.json").read_text(encoding="utf-8"))
source = json.loads((BASE / "source.json").read_text(encoding="utf-8"))
segs = sorted((json.loads(l) for l in (BASE / "segments.v1.jsonl").open(encoding="utf-8")),
              key=lambda s: s["start"])

beats = {b["id"]: b for b in beats_doc["beats"]}
queue = qdoc.get("queue", [])
findings = []


def add(item, sev, cat, msg):
    findings.append((item, sev, cat, msg))


def mmss(t):
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


# ---- document-level -------------------------------------------------------
recorded = source.get("recorded")
if qdoc.get("recorded") != recorded:
    add("-", "HIGH", "recorded-date",
        f"queue says recorded {qdoc.get('recorded')!r}, source.json says {recorded!r}")

# A question cut at a gate stays in the file so nothing is lost, but it will not
# run, so it does not spend budget and does not count as covering its beat.
def live(items):
    return [i for i in items if (i.get("human") or {}).get("decision") != "cut"]


touched = any(q.get("human") for q in queue)
live_queue = live(queue)
n_cut = len(queue) - len(live_queue)

if not (QUEUE_MIN <= len(live_queue) <= QUEUE_MAX):
    add("-", "HIGH", "budget",
        f"{len(live_queue)} live questions"
        + (f" ({n_cut} cut)" if n_cut else "")
        + f", budget is {QUEUE_MIN}-{QUEUE_MAX} (research-pass.md §6)")

ids = [q.get("id") for q in queue]
if len(set(ids)) != len(ids):
    add("-", "HIGH", "duplicate-id", "duplicate queue ids")

qtexts = {}
for q in queue:
    t = re.sub(r"\s+", " ", (q.get("question") or "").strip().lower())
    if t and t in qtexts:
        add(q.get("id", "?"), "HIGH", "duplicate-question",
            f"same question text as {qtexts[t]}")
    qtexts[t] = q.get("id", "?")

# The cold-open trap. Anything before program_start on the master timeline is
# audio that was moved there from elsewhere.
program_start = (source.get("structure") or {}).get("program_start")
rule7 = [p.lower() for p in qdoc.get("rule7_forbidden", [])]

# ---- per item -------------------------------------------------------------
# Live items only. A cut question is not going to run, and its defects are
# usually the reason it was cut -- re-reporting them would make every gate
# decision turn the build red.
for q in live_queue:
    qid = q.get("id", "?")
    if not re.fullmatch(r"r\d\d", str(qid)):
        add(qid, "MED", "id-format", "id is not rNN")

    typ = q.get("type")
    if typ not in TYPES:
        add(qid, "HIGH", "type", f"{typ!r} not one of {sorted(TYPES)}")

    feeds = q.get("feeds")
    if feeds not in FEEDS:
        add(qid, "HIGH", "feeds", f"{feeds!r} not one of {sorted(FEEDS)}")

    if not (q.get("question") or "").strip():
        add(qid, "HIGH", "question-empty", "no question")
    for field in ("why", "expected"):
        if not (q.get(field) or "").strip():
            add(qid, "MED", field + "-empty", f"no {field}")

    bid = q.get("beat")
    b = beats.get(bid)
    if b is None:
        add(qid, "HIGH", "beat-missing", f"beat {bid!r} is not in beats.v1.json")
        continue

    t = q.get("anchor_t")
    if t is None:
        add(qid, "MED", "anchor-missing", "no anchor_t")
    else:
        if program_start is not None and t < program_start:
            if "source_anchor_t" not in q:
                add(qid, "HIGH", "cold-open-anchor",
                    f"anchor_t={t} is before program_start {program_start}; that audio was "
                    "MOVED from elsewhere, so the question would be asked about the wrong "
                    "moment. Anchor it on the source timeline instead")
        # The window is the clip; the anchor is evidence. A research anchor may sit
        # outside the beat's window -- beats already cite segments outside theirs --
        # but it has to say so, and say why.
        if not (b["t"] - 0.001 <= t <= b["t_end"] + 0.001):
            if not q.get("anchor_outside_window"):
                add(qid, "HIGH", "anchor-outside-beat",
                    f"anchor_t={t} is outside {bid}'s window [{b['t']}, {b['t_end']}] and "
                    "does not declare anchor_outside_window")
            elif not (q.get("anchor_reason") or "").strip():
                add(qid, "HIGH", "anchor-undeclared",
                    "anchor_outside_window is set but anchor_reason is empty")
        elif q.get("anchor_outside_window"):
            add(qid, "MED", "anchor-declared-inside",
                f"anchor_outside_window is set but anchor_t={t} is inside {bid}'s window")

    for extra in (q.get("also_at") or []):
        if not any(s["start"] - 0.05 <= extra <= s["end"] + 0.05 for s in segs):
            add(qid, "MED", "also-at-no-segment", f"also_at {extra} lands inside no segment")
        if not any(s["start"] - 0.05 <= t <= s["end"] + 0.05 for s in segs):
            add(qid, "MED", "anchor-no-segment", f"anchor_t={t} lands inside no segment")
        label = q.get("anchor_label")
        if label and not label.startswith("source ") and label != mmss(t):
            add(qid, "HIGH", "anchor-label",
                f"anchor_label {label!r} does not match anchor_t {t} ({mmss(t)})")

    guards = (q.get("guards") or "")
    if typ == "since":
        if recorded and recorded not in guards and "after" not in guards.lower():
            add(qid, "MED", "since-rule",
                "a `since` must require a source published after the recording date "
                "(research-pass.md §1); guards do not say so")

    # Rule 7: never check something the speaker did not assert.
    qlow = (q.get("question") or "").lower()
    for phrase in rule7:
        if phrase and phrase in qlow:
            add(qid, "HIGH", "rule7-violation",
                f"question targets {phrase!r}, which rule7_forbidden lists as a "
                "non-assertion (invented number, rounding, or prediction)")

    # If the beat itself flagged rule 7, the item must carry the guard forward.
    rp = (b.get("research_potential") or "")
    if re.search(r"rule 7|do not check|do NOT fact-check", rp, re.I):
        if "rule 7" not in guards.lower():
            add(qid, "HIGH", "rule7-guard-dropped",
                f"{bid}'s research_potential invokes rule 7 but this item's guards do not "
                "carry it forward to 4b")

# ---- cross-item -----------------------------------------------------------
by_beat = {}
for q in live_queue:
    by_beat.setdefault(q.get("beat"), []).append(q)

for bid, items in by_beat.items():
    tendril_feeding = [q for q in items if "tendril" in (q.get("feeds") or "")]
    if len(tendril_feeding) > MAX_TENDRILS_PER_BEAT:
        add(bid, "MED", "tendril-cap",
            f"{len(tendril_feeding)} tendril-feeding items; rule 3 caps tendrils at "
            f"{MAX_TENDRILS_PER_BEAT} per beat")
    seen = {}
    for q in items:
        key = q.get("type")
        if key in seen:
            add(q.get("id", "?"), "MED", "same-beat-same-type",
                f"{bid} already has a {key} item ({seen[key]}); make sure they produce "
                "different artifacts")
        seen[key] = q.get("id", "?")

uncovered = [bid for bid in beats if bid not in by_beat]
# A beat deliberately held out and recorded as such is a decision; a beat that
# simply fell off the queue is a defect. Only the second one is worth a MED.
held = {h.get("beat") for h in
        ((qdoc.get("source_timeline_items") or {}).get("held") or [])}
forgotten = [bid for bid in uncovered if bid not in held]
if forgotten:
    add("-", "MED", "beat-uncovered", f"no queue item for {sorted(forgotten)}")
for bid in sorted(b for b in uncovered if b in held):
    add("-", "LOW", "beat-held",
        f"{bid} has no queue item, held deliberately with a reason recorded")

by_type = {}
for q in live_queue:
    by_type[q.get("type")] = by_type.get(q.get("type"), 0) + 1

if recorded:
    age = 2026 - int(recorded[:4])
    if age >= SINCE_AGE_YEARS and by_type.get("since", 0) < 2:
        add("-", "HIGH", "since-shape",
            f"convo is ~{age} years old and has {by_type.get('since', 0)} `since` items; "
            "the archive value is the whole reason to start with the back catalogue "
            "(research-pass.md §1)")

# The coverage block is 4a's record of what it proposed. Once a human has
# decided anything it is history, not a claim about the current queue, so drift
# is expected and only checked while the extract output is still pristine.
cov = qdoc.get("coverage") or {}
if cov and not touched:
    if cov.get("by_type") and cov["by_type"] != {**{t: 0 for t in TYPES}, **by_type}:
        add("-", "MED", "coverage-drift",
            f"coverage.by_type {cov.get('by_type')} != actual {by_type}")
    if cov.get("beats_with_items") is not None and cov["beats_with_items"] != len(by_beat):
        add("-", "MED", "coverage-drift",
            f"coverage.beats_with_items {cov['beats_with_items']} != actual {len(by_beat)}")
    if cov.get("beats_without_items") is not None and \
            sorted(cov["beats_without_items"]) != sorted(uncovered):
        add("-", "MED", "coverage-drift",
            f"coverage.beats_without_items {cov['beats_without_items']} != actual "
            f"{sorted(uncovered)}")

# ---- decision ledger ------------------------------------------------------
# A queue that only lists survivors cannot be audited. Every candidate gets a
# fate and an enumerable reason code -- prose does not aggregate, and §4 wants
# this as a training set.
FATES = {"queued", "folded", "held", "rejected", "bounced"}
dec = qdoc.get("decisions") or {}
codes = set(dec.get("reason_codes") or [])
queue_ids = {q.get("id") for q in queue}

if not dec.get("entries"):
    add("-", "MED", "ledger-missing",
        "no decisions.entries; rejected candidates leave no trace and cannot be audited")

for i, e in enumerate(dec.get("entries") or []):
    tag = e.get("was") or e.get("candidate", f"entry{i}")[:34]
    fate = e.get("fate")
    if fate not in FATES:
        add(tag, "HIGH", "ledger-fate", f"{fate!r} not one of {sorted(FATES)}")
    if fate == "queued":
        add(tag, "MED", "ledger-fate",
            "queued items belong in `queue`, not the ledger")
    code = e.get("reason_code")
    if code not in codes:
        add(tag, "HIGH", "ledger-reason-code",
            f"{code!r} is not in decisions.reason_codes {sorted(codes)}")
    if not (e.get("reason") or "").strip():
        add(tag, "MED", "ledger-reason-empty", "no reason prose")
    into = e.get("into")
    if into and into not in queue_ids:
        add(tag, "HIGH", "ledger-into",
            f"folded into {into!r}, which is not a live queue id")
    if code == "covered-by" and not into:
        add(tag, "MED", "ledger-into",
            "reason_code covered-by but no `into` naming what covers it")
    was = e.get("was")
    if was and was in queue_ids:
        add(tag, "HIGH", "ledger-contradiction",
            f"ledger says {was} was removed, but {was} is still in the queue")

for e in (dec.get("bounced") or []):
    if e.get("stage") not in ("gate1", "gate2"):
        add(e.get("was", "bounced"), "MED", "ledger-bounced",
            "bounced entries record a human decision and must carry stage gate1 or gate2")

# ---- entity candidates ----------------------------------------------------
# Entities are not tendrils: they are orientation, exempt from the per-beat cap
# and the one-domain rule. The price of that exemption is that the term must
# actually be SAID on tape -- a thing described but never named is an
# `identify` question, not a glossary box.
ent = qdoc.get("entity_candidates") or {}
MASTER_TEXT = " ".join(s["text"] for s in segs).lower()
seen_terms = set()
for c in (ent.get("candidates") or []):
    eid = c.get("id", "?")
    term = c.get("term", "")
    if term.lower() in seen_terms:
        add(eid, "MED", "entity-duplicate", f"{term!r} listed twice")
    seen_terms.add(term.lower())

    said = c.get("said_as") or []
    if not said:
        add(eid, "HIGH", "entity-said-as", f"{term!r} has no said_as")
    elif not any(re.search(r"\b" + re.escape(s), MASTER_TEXT) for s in
                 (x.lower() for x in said)):
        add(eid, "HIGH", "entity-not-spoken",
            f"none of said_as {said} appears in the transcript; a thing described but "
            "never named is an `identify` question, not an entity box")

    ft = c.get("first_t")
    if ft is None:
        add(eid, "MED", "entity-anchor", "no first_t")
    else:
        if not any(s["start"] - 0.05 <= ft <= s["end"] + 0.05 for s in segs):
            add(eid, "MED", "entity-anchor", f"first_t={ft} lands inside no segment")
        lbl = c.get("first_label")
        if lbl and lbl != mmss(ft):
            add(eid, "HIGH", "entity-label",
                f"first_label {lbl!r} does not match first_t {ft} ({mmss(ft)})")

    eb = c.get("beat")
    if eb is not None and eb not in beats:
        add(eid, "HIGH", "entity-beat", f"beat {eb!r} is not in beats.v1.json")

cap = ent.get("proposed_cap")
n_ent = len(ent.get("candidates") or [])
if cap and n_ent > cap:
    add("-", "LOW", "entity-cap",
        f"{n_ent} candidates proposed against a ship cap of {cap}; the human gate picks")

# ---- gleanings ------------------------------------------------------------
# What the harvest left in the field. The `unnamed` check is the exact inverse
# of the entity check above: an entity's term must be spoken, a gleaning's term
# must not be, so no term can be filed as both.
GLEAN_KINDS = {"unnamed", "dropped", "implied", "cut"}
CUT_TEXT = (BASE / "cut-material.v1.md").read_text(encoding="utf-8").lower()


def norm(t):
    t = t.lower().replace("’", "'").replace("‘", "'")
    t = t.replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", t)


NORM_MASTER, NORM_CUT = norm(MASTER_TEXT), norm(CUT_TEXT)

gl = qdoc.get("gleaning_candidates") or {}
gcands = gl.get("candidates") or []
gcap = gl.get("cap")
if gcap and len(gcands) > gcap:
    add("-", "MED", "gleaning-cap",
        f"{len(gcands)} gleanings against a cap of {gcap}; without scarcity this is a junk drawer")

for c in gcands:
    gid = c.get("id", "?")
    kind = c.get("kind")
    if kind not in GLEAN_KINDS:
        add(gid, "HIGH", "gleaning-kind", f"{kind!r} not one of {sorted(GLEAN_KINDS)}")

    has_t, has_st = c.get("t") is not None, c.get("source_t") is not None
    if has_t == has_st:
        add(gid, "HIGH", "gleaning-anchor",
            "exactly one of t (master) or source_t (mix/raw-track) is required")
    if has_t:
        if not any(s["start"] - 0.05 <= c["t"] <= s["end"] + 0.05 for s in segs):
            add(gid, "MED", "gleaning-anchor", f"t={c['t']} lands inside no segment")
        lbl = c.get("label")
        if lbl and not lbl.startswith("source ") and lbl != mmss(c["t"]):
            add(gid, "HIGH", "gleaning-label",
                f"label {lbl!r} does not match t {c['t']} ({mmss(c['t'])})")
    if has_st and kind != "cut":
        add(gid, "MED", "gleaning-anchor",
            f"source_t is for material the master cannot address; kind is {kind!r}, not 'cut'")

    # Evidence, or it is the model editorialising about a conversation.
    quote = c.get("quote") or ""
    if not quote.strip():
        add(gid, "HIGH", "gleaning-quote", "no quote; a gleaning without evidence is an opinion")
    else:
        hay = NORM_CUT if has_st else NORM_MASTER
        frags = [f for f in (x.strip() for x in norm(quote).split("...")) if f]
        if not all(f in hay for f in frags):
            add(gid, "HIGH", "gleaning-quote-not-found",
                f'not verbatim in {"cut material" if has_st else "the transcript"}: '
                f'"{quote[:60]}"')

    if kind == "unnamed":
        term = (c.get("term") or "").strip()
        if not term:
            add(gid, "HIGH", "gleaning-term", "kind `unnamed` requires the term they never said")
        elif re.search(r"\b" + re.escape(term.lower()), NORM_MASTER):
            add(gid, "HIGH", "gleaning-actually-named",
                f"{term!r} DOES appear in the transcript, so it was named; that is an entity "
                "box, not an unnamed gleaning")

    if not (c.get("note") or "").strip():
        add(gid, "MED", "gleaning-note", "no note saying what was in hand and not taken")
    elif (c.get("note") or "").strip().endswith("?"):
        add(gid, "MED", "gleaning-reads-as-seed",
            "note is phrased as a question; a question for a future convo is a seed")

    rb = c.get("resolved_by")
    if rb is not None and rb not in queue_ids:
        add(gid, "HIGH", "gleaning-resolved-by",
            f"resolved_by {rb!r} is not a live queue id")

    gb = c.get("beat")
    if gb is not None and gb not in beats:
        add(gid, "HIGH", "gleaning-beat", f"beat {gb!r} is not in beats.v1.json")

# A term cannot be both a box and an unnamed gleaning.
glean_terms = {(c.get("term") or "").lower() for c in gcands if c.get("kind") == "unnamed"}
for c in (ent.get("candidates") or []):
    if (c.get("term") or "").lower() in glean_terms:
        add(c.get("id", "?"), "HIGH", "entity-gleaning-collision",
            f"{c.get('term')!r} is filed as both an entity box and an unnamed gleaning")

rank = {"HIGH": 0, "MED": 1, "LOW": 2}
findings.sort(key=lambda f: (rank[f[1]], str(f[0])))
print(f"{len(findings)} queue findings across {len(queue)} questions\n" if findings
      else f"PASS: no structural findings across {len(queue)} questions.")
for qid, sev, cat, msg in findings:
    print(f"[{sev:4}] {str(qid):5} {cat:22} {msg}")

n_hi = sum(1 for f in findings if f[1] == "HIGH")
n_med = sum(1 for f in findings if f[1] == "MED")
print(f"\nHIGH={n_hi} MED={n_med}")
print(f"types: {dict(sorted(by_type.items()))}")

gate = ((qdoc.get("provenance") or {}).get("human_gate") or {}).get("decision")
print(f"\nGATE 1: {'OPEN — not approved, 4b must not run' if not gate else gate}")

if args.json:
    args.json.write_text(json.dumps({
        "convo": qdoc.get("convo"),
        "stage": "4a-verify",
        "checks": "structural only — cannot judge whether a question is a good question, "
                  "which is what the Gate 1 human review is for",
        "sources": ["research-queue.v1.json", "beats.v1.json", "source.json",
                    "segments.v1.jsonl"],
        "questions_checked": len(queue),
        "by_type": dict(sorted(by_type.items())),
        "gate_1": gate or "open",
        "counts": {"HIGH": n_hi, "MED": n_med},
        "findings": [{"item": i, "severity": s, "category": c, "detail": m}
                     for i, s, c, m in findings],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {args.json}")

sys.exit(1 if n_hi else 0)
