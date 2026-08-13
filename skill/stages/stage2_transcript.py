#!/usr/bin/env python3
"""Stage 2 — transcribe.

Reads a word-level ASR result and writes the two artifacts stage 3 consumes:

    transcript.v1.md    speaker-attributed, timestamped, human-readable
    segments.v1.jsonl   one JSON object per speaker turn, machine-readable

Idempotent: both outputs are written whole, never appended. Re-running against
the same input produces byte-identical files.

No third-party dependencies. Matches the fallback renderer's constraint.

Input formats
-------------
ElevenLabs Scribe (`--asr scribe`, default) — the shape produced by the
`speech_to_text` endpoint with diarization on:

    {"words": [{"text","start","end","type","speaker_id","logprob"}, ...],
     "audio_duration_secs": float}

`type` is one of word | spacing | audio_event. Spacing is dropped; audio events
are kept inline in the text and also listed per turn.

Speaker mapping
---------------
Diarization emits opaque ids (speaker_0, speaker_1). The mapping to person ids
is supplied with --map and is a claim that must be evidenced, not guessed. The
default mapping for zengineering-098 was established from five self-identifying
content anchors in the transcript; see PROVENANCE below and the note written
into the output header.

speaker_confidence follows docs/convo-v1-spec.md §9:

    confirmed   attribution comes from per-track audio ownership
    inferred    attribution comes from a diarization model

Diarization is `inferred` no matter how well it agrees with a human pass, so
that is what this stage writes unless --confidence is given explicitly. A
cross-check file (--check, e.g. the hand-labelled speakers.md) does not upgrade
the confidence; it only reports disagreements, which are recorded per turn in
the `disputed` field and summarised on stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

DEFAULT_MAP = {"speaker_0": "tbj", "speaker_1": "adam"}

PROVENANCE = (
    "Diarized speaker ids were mapped to people by self-identification in the "
    "transcript: 'I'm Adam' (21.2s), 'I'm Brian' (22.3s), 'Juris is "
    "increasingly' (130.4s), 'I was a manufacturing engineer' (2892.3s), "
    "'people with legal training like me' (3437.1s). Five anchors, no "
    "contradictions. The mapping is evidenced; the turn boundaries are still a "
    "model's, so confidence stays `inferred` until per-track audio is used."
)


def hhmmss(t: float) -> str:
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


def load_scribe(path: str) -> tuple[list[dict], float]:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc["words"], float(doc.get("audio_duration_secs") or 0.0)


def turns_from_words(words: list[dict], speaker_map: dict[str, str]) -> list[dict]:
    """Group the word stream into speaker turns.

    A turn ends when speaker_id changes. Spacing tokens carry no information
    and are dropped; the text is rebuilt from word and audio_event tokens.
    """
    turns: list[dict] = []
    cur: dict | None = None

    for tok in words:
        kind = tok.get("type")
        if kind == "spacing":
            continue
        sid = tok.get("speaker_id")
        if cur is None or cur["_sid"] != sid:
            cur = {
                "_sid": sid,
                "speaker": speaker_map.get(sid, sid),
                "start": float(tok["start"]),
                "end": float(tok["end"]),
                "_tokens": [],
                "_logprobs": [],
                "events": [],
            }
            turns.append(cur)
        cur["end"] = float(tok["end"])
        cur["_tokens"].append(tok["text"])
        if kind == "audio_event":
            cur["events"].append(tok["text"])
        else:
            lp = tok.get("logprob")
            if lp is not None:
                cur["_logprobs"].append(float(lp))

    out = []
    for i, t in enumerate(turns, 1):
        text = " ".join(t["_tokens"])
        text = re.sub(r"\s+([,.!?;:])", r"\1", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        lps = t["_logprobs"]
        out.append(
            {
                "id": f"s{i:04d}",
                "speaker": t["speaker"],
                "start": round(t["start"], 2),
                "end": round(t["end"], 2),
                "text": text,
                "words": len(lps),
                "events": t["events"],
                "logprob_min": round(min(lps), 4) if lps else None,
                "logprob_mean": round(sum(lps) / len(lps), 4) if lps else None,
                "_sid": t["_sid"],
            }
        )
    return out


CHECK_TURN = re.compile(r"^\*\*(?P<who>[^*]+)\*\*\s+_\[(?P<ts>\d\d:\d\d:\d\d)\]_\s*$")


def load_check(path: str, alias: dict[str, str]) -> list[tuple[int, str]]:
    """Parse a hand-labelled transcript into (seconds, person_id) turn heads."""
    heads = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = CHECK_TURN.match(line.strip())
            if not m:
                continue
            h, mi, s = (int(x) for x in m.group("ts").split(":"))
            who = m.group("who").strip()
            heads.append((h * 3600 + mi * 60 + s, alias.get(who.lower(), who.lower())))
    return heads


def apply_check(turns: list[dict], heads: list[tuple[int, str]], tol: float = 1.5) -> int:
    """Flag turns whose speaker disagrees with the hand-labelled pass.

    Both sequences are turn-ordered, so they are walked together monotonically.
    Nearest-timestamp matching is wrong here: rapid back-and-forth puts turns
    less than `tol` apart and a nearest match silently pairs a turn with its
    neighbour, which manufactures disagreements that do not exist.

    Timestamps in a hand-labelled pass are usually truncated to whole seconds,
    so a head matches a turn when it is within `tol`. A turn with no match is
    left unflagged — absence of a label is not disagreement.
    """
    disputes = 0
    j = 0
    for t in turns:
        while j + 1 < len(heads) and heads[j][0] < t["start"] - tol:
            j += 1
        who = heads[j][1] if j < len(heads) and abs(heads[j][0] - t["start"]) <= tol else None
        t["disputed"] = bool(who and who != t["speaker"])
        if t["disputed"]:
            t["disputed_alt"] = who
            disputes += 1
        if who is not None:
            j += 1
    return disputes


def write_segments(path: str, turns: list[dict], confidence: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        for t in turns:
            rec = {k: v for k, v in t.items() if not k.startswith("_")}
            rec["speaker_confidence"] = confidence
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


def write_transcript(
    path: str,
    turns: list[dict],
    meta: dict,
    confidence: str,
    disputes: int,
) -> None:
    names = meta["names"]
    lines = [
        f"# {meta['title']}",
        "",
        f"**Recorded:** {meta['recorded']} · **Published:** {meta['published']} · "
        f"**Runtime:** {hhmmss(meta['duration'])}",
        f"**Speakers:** {' , '.join(f'{v} (`{k}`)' for k, v in names.items())}",
        f"**Source:** {meta['audio']}",
        "",
        f"> Machine transcript. {meta['transcriber']}",
        f"> Speaker attribution: `{confidence}`. {meta['attribution_note']}",
    ]
    if disputes:
        lines.append(
            f"> {disputes} turn(s) disagree with the hand-labelled pass and are "
            f"marked `disputed` in `segments.v1.jsonl`."
        )
    lines += ["", "---", ""]

    for t in turns:
        lines.append(f"**{names.get(t['speaker'], t['speaker'])}** _[{hhmmss(t['start'])}]_")
        lines.append("")
        lines.append(t["text"])
        lines.append("")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--asr", default="scribe", choices=["scribe"])
    p.add_argument("--input", required=True, help="word-level ASR json")
    p.add_argument("--outdir", required=True, help="convo directory")
    p.add_argument("--map", default=None, help='e.g. "speaker_0=tbj,speaker_1=adam"')
    p.add_argument("--names", default="adam=Adam Kerpelman,tbj=T. Brian Jones")
    p.add_argument("--check", default=None, help="hand-labelled transcript to cross-check against")
    p.add_argument("--check-alias", default="adam=adam,tbj=tbj,brian=tbj")
    p.add_argument("--confidence", default="inferred", choices=["confirmed", "inferred"])
    p.add_argument("--title", default="")
    p.add_argument("--recorded", default="")
    p.add_argument("--published", default="")
    p.add_argument("--audio", default="")
    p.add_argument("--version", default="v1")
    args = p.parse_args()

    def kv(s: str) -> dict[str, str]:
        return dict(part.split("=", 1) for part in s.split(",") if part)

    speaker_map = kv(args.map) if args.map else dict(DEFAULT_MAP)
    names = kv(args.names)

    words, duration = load_scribe(args.input)
    turns = turns_from_words(words, speaker_map)

    disputes = 0
    if args.check:
        disputes = apply_check(turns, load_check(args.check, kv(args.check_alias)))
    else:
        for t in turns:
            t["disputed"] = False

    os.makedirs(args.outdir, exist_ok=True)
    seg_path = os.path.join(args.outdir, f"segments.{args.version}.jsonl")
    txt_path = os.path.join(args.outdir, f"transcript.{args.version}.md")

    write_segments(seg_path, turns, args.confidence)
    write_transcript(
        txt_path,
        turns,
        {
            "title": args.title,
            "recorded": args.recorded,
            "published": args.published,
            "audio": args.audio,
            "duration": duration,
            "names": names,
            "transcriber": "ElevenLabs Scribe, word-level timings, diarization on.",
            "attribution_note": PROVENANCE,
        },
        args.confidence,
        disputes,
    )

    spoken = {}
    for t in turns:
        spoken[t["speaker"]] = spoken.get(t["speaker"], 0.0) + (t["end"] - t["start"])
    print(
        json.dumps(
            {
                "stage": 2,
                "turns": len(turns),
                "words": sum(t["words"] for t in turns),
                "duration_s": round(duration, 2),
                "talk_seconds": {k: round(v) for k, v in sorted(spoken.items())},
                "speaker_confidence": args.confidence,
                "disputed_turns": disputes,
                "outputs": [seg_path, txt_path],
                "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            indent=2,
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
