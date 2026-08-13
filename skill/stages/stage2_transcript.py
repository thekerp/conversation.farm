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

Diarization alone is `inferred` no matter how well it agrees with another text
pass. Only per-track audio ownership earns `confirmed`, and `--confidence
confirmed` therefore requires `--confidence-method` describing how it was
established.

`--overrides` takes stage 2c's output, where the per-track audio disagreed with
the diarizer. Stage 2c never writes the transcript itself: this stage stays the
only writer, so re-running it cannot silently undo the arbitration.

`--check` cross-checks against another labelled transcript. It does not upgrade
confidence — a second text pass derived from the same diarization corroborates
nothing. Disagreements land in the per-turn `disputed` field.
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
    "contradictions. This establishes which id is which person; it does not "
    "establish that the model drew the turn boundaries correctly. Only stage 2c "
    "does that, from the per-track audio."
)


def hhmmss(t: float) -> str:
    t = int(t)
    return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"


def load_scribe(path: str) -> tuple[list[dict], float]:
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc["words"], float(doc.get("audio_duration_secs") or 0.0)


def in_window(t: float, windows: list[dict]) -> bool:
    return any(w["start"] <= t < w["end"] for w in windows)


def turns_from_words(
    words: list[dict],
    speaker_map: dict[str, str],
    music: list[dict] | None = None,
    lexicon: list[dict] | None = None,
) -> tuple[list[dict], int, int]:
    """Group the word stream into speaker turns.

    A turn ends when speaker_id changes. Spacing tokens carry no information
    and are dropped; the text is rebuilt from word and audio_event tokens.

    `music` windows are regions where the session carries a music bed and no
    voice clip. Diarization has no concept of "not a person", so it attributes
    the vocal of the music to whichever speaker it resembles. Those words are
    dropped: they are not speech by a participant, and leaving them in inflates
    talk time and fuses song lyrics onto the front of a real turn.

    `lexicon` entries repair known ASR errors at a specific timestamp. Kept in
    data rather than applied by hand so the transcript stays reproducible.
    """
    music = music or []
    lex = {round(float(e["t"]), 2): e for e in (lexicon or [])}

    turns: list[dict] = []
    cur: dict | None = None
    dropped = 0
    repaired = 0

    for tok in words:
        kind = tok.get("type")
        if kind == "spacing":
            continue
        mid = (float(tok["start"]) + float(tok["end"])) / 2
        if in_window(mid, music):
            if kind == "word":
                dropped += 1
            continue
        entry = lex.get(round(float(tok["start"]), 2))
        if entry and entry["from"] in tok["text"]:
            tok = dict(tok, text=tok["text"].replace(entry["from"], entry["to"]))
            repaired += 1
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
    return out, dropped, repaired


def attach_annotations(turns: list[dict], annotations: list[dict]) -> int:
    """Hang known speaker slips and self-repairs on the turns they fall inside.

    These never alter the text. A misspoken referent is a fact about the
    conversation and stage 4 has to see it, or it researches the wrong subject.
    """
    n = 0
    for t in turns:
        hits = [
            {k: a[k] for k in ("said", "means", "kind", "why") if k in a}
            for a in annotations
            if a["start"] < t["end"] and a["end"] >= t["start"]
        ]
        if hits:
            t["annotations"] = hits
            n += len(hits)
    return n


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
    if meta.get("dropped"):
        lines.append(
            f"> {meta['dropped']} word(s) of music-bed vocal removed — the diarizer had "
            f"attributed the song to a participant. See `corrections.json`."
        )
    if meta.get("repaired"):
        lines.append(
            f"> {meta['repaired']} ASR error(s) repaired from `corrections.json`."
        )
    if meta.get("overridden"):
        lines.append(
            f"> {meta['overridden']} turn(s) reassigned by per-track audio over the diarizer's "
            f"label. See `speaker-arbitration.v1.json`."
        )
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
    p.add_argument("--corrections", default=None, help="corrections.json: music windows, lexicon, annotations")
    p.add_argument("--overrides", default=None, help="speaker-overrides.v1.json from stage 2c")
    p.add_argument("--confidence", default="inferred", choices=["confirmed", "inferred"])
    p.add_argument("--confidence-method", default="", help="required when --confidence confirmed")
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

    if args.confidence == "confirmed" and not args.confidence_method:
        p.error("--confidence confirmed requires --confidence-method: how ownership was established")

    corr = {}
    if args.corrections:
        with open(args.corrections, encoding="utf-8") as fh:
            corr = json.load(fh)

    words, duration = load_scribe(args.input)
    turns, dropped, repaired = turns_from_words(
        words, speaker_map, corr.get("music_windows"), corr.get("lexicon")
    )
    annotated = attach_annotations(turns, corr.get("annotations", []))

    overridden = 0
    for t in turns:
        t["speaker_source"] = "diarization"
    if args.overrides:
        with open(args.overrides, encoding="utf-8") as fh:
            ov = json.load(fh)
        by_t = {round(float(o["t"]), 2): o for o in ov.get("overrides", [])}
        for t in turns:
            o = by_t.get(round(t["start"], 2))
            if o and o["speaker"] != t["speaker"]:
                t["speaker"] = o["speaker"]
                t["speaker_source"] = "per_track_audio"
                t["audio_margin_db"] = o.get("margin_db")
                overridden += 1

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
            "attribution_note": args.confidence_method or PROVENANCE,
            "dropped": dropped,
            "repaired": repaired,
            "overridden": overridden,
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
                "music_words_dropped": dropped,
                "asr_words_repaired": repaired,
                "annotations_attached": annotated,
                "speaker_overrides_applied": overridden,
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
