#!/usr/bin/env python3
"""Stage 2c — arbitrate speaker labels against the per-track audio.

Diarization guesses who is talking from one mixed signal. Isolated per-speaker
tracks *know*. This stage walks every turn, measures each speaker's energy on
their own track over that turn's window, and overrides the diarizer where the
audio is unambiguous.

The catch is that turn timestamps are on the published master and the tracks are
on the session timeline, and a published episode is an edit. Windows are mapped
through `source.json` -> `edit_map`, and a turn that straddles a cut is scored
only on its longest surviving piece.

Where the two tracks are close, the audio is not evidence — that is simultaneous
speech, and this stage leaves the diarizer's answer alone rather than flipping a
coin. Every turn gets `speaker_source` recording which decided it.

Idempotent. Requires ffmpeg. No third-party libraries.

    python3 skill/stages/stage2c_arbitrate_speakers.py \
        --convo convos/zengineering-098 --segments segments.v1.jsonl
"""

from __future__ import annotations

import argparse
import array
import json
import math
import os
import subprocess
import sys

FRAME_HZ = 100  # 10 ms envelope frames
SR = 8000
FRAME_SHIFT = 0.0784  # .sesx sample positions -> ffmpeg decode frame of the final mix


def envelope(path: str) -> array.array:
    """Decode a track to a 10 ms mean-square envelope."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "-acodec", "pcm_s16le", "-"],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {path}: {proc.stderr[-500:]!r}")
    pcm = array.array("h")
    pcm.frombytes(proc.stdout)
    step = SR // FRAME_HZ
    env = array.array("d")
    for i in range(0, len(pcm) - step + 1, step):
        acc = 0.0
        for s in pcm[i:i + step]:
            acc += float(s) * s
        env.append(acc / step)
    return env


def window_db(env: array.array, start: float, end: float) -> float:
    a, b = int(start * FRAME_HZ), int(end * FRAME_HZ)
    a, b = max(0, a), min(len(env), b)
    if b <= a:
        return -99.0
    acc = 0.0
    for i in range(a, b):
        acc += env[i]
    ms = acc / (b - a)
    return 10 * math.log10(ms / (32768.0 ** 2)) if ms > 0 else -99.0


def master_to_mix(clips: list[dict], m: float) -> float | None:
    for c in clips:
        if c["master_in"] <= m < c["master_out"]:
            return m + (c["mix_in"] - c["master_in"])
    return None


def longest_mapped_span(clips: list[dict], start: float, end: float) -> tuple[float, float] | None:
    """Longest piece of [start,end) that lies inside a single master clip."""
    best = None
    for c in clips:
        lo, hi = max(start, c["master_in"]), min(end, c["master_out"])
        if hi - lo <= 0:
            continue
        if best is None or (hi - lo) > (best[1] - best[0]):
            off = c["mix_in"] - c["master_in"]
            best = (lo + off, hi + off)
    return best


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--convo", required=True)
    p.add_argument("--segments", default="segments.v1.jsonl")
    p.add_argument("--margin-db", type=float, default=6.0,
                   help="decisive separation; below this the audio is not evidence")
    p.add_argument("--min-seconds", type=float, default=0.35,
                   help="windows shorter than this are too short to score")
    p.add_argument("--report", default="speaker-arbitration.v1.json")
    p.add_argument("--overrides", default="speaker-overrides.v1.json",
                   help="written for stage 2 to consume; stage 2 stays the only writer of the transcript")
    args = p.parse_args()

    with open(os.path.join(args.convo, "source.json"), encoding="utf-8") as fh:
        src = json.load(fh)
    clips = src["edit_map"]["clips"]

    seg_path = os.path.join(args.convo, args.segments)
    segs = [json.loads(l) for l in open(seg_path, encoding="utf-8")]

    people = list(src["participants"])
    envs = {}
    for who in people:
        track = os.path.join(args.convo, src["tracks"][who])
        print(f"decoding {who}: {os.path.basename(track)}", file=sys.stderr)
        envs[who] = envelope(track)

    changed, kept, unscored, ambiguous = [], 0, 0, 0
    for s in segs:
        span = longest_mapped_span(clips, s["start"], s["end"])
        if span is None or (span[1] - span[0]) < args.min_seconds:
            s["speaker_source"] = "diarization"
            s["audio_margin_db"] = None
            unscored += 1
            continue
        db = {who: window_db(envs[who], span[0], span[1]) for who in people}
        loud = max(db, key=db.get)
        others = [v for k, v in db.items() if k != loud]
        margin = db[loud] - max(others)
        s["audio_margin_db"] = round(margin, 1)
        if margin < args.margin_db:
            s["speaker_source"] = "diarization"
            ambiguous += 1
        elif loud != s["speaker"]:
            changed.append({"id": s["id"], "t": s["start"], "from": s["speaker"], "to": loud,
                            "margin_db": round(margin, 1), "text": s["text"][:90]})
            s["speaker"] = loud
            s["speaker_source"] = "per_track_audio"
        else:
            s["speaker_source"] = "per_track_audio"
            kept += 1

    talk: dict[str, float] = {}
    for s in segs:
        talk[s["speaker"]] = talk.get(s["speaker"], 0.0) + (s["end"] - s["start"])

    report = {
        "convo": src["id"],
        "method": f"Per-track RMS over each turn's window, mapped master->mix through edit_map. "
                  f"Decisive margin {args.margin_db} dB; below that the diarizer's label stands "
                  f"because that is simultaneous speech, not a mislabel.",
        "turns": len(segs),
        "confirmed_by_audio": kept,
        "changed_by_audio": len(changed),
        "left_to_diarization_ambiguous": ambiguous,
        "left_to_diarization_unscorable": unscored,
        "talk_seconds": {k: round(v) for k, v in sorted(talk.items())},
        "changes": changed,
    }
    with open(os.path.join(args.convo, args.report), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    overrides = {
        "note": "Speaker labels the per-track audio overrides on the diarizer. Consumed by "
                "stage2_transcript.py --overrides, so the transcript has exactly one writer and "
                "re-running stage 2 does not silently undo this pass.",
        "method": report["method"],
        "overrides": [
            {"t": c["t"], "speaker": c["to"], "was": c["from"], "margin_db": c["margin_db"]}
            for c in changed
        ],
    }
    with open(os.path.join(args.convo, args.overrides), "w", encoding="utf-8") as fh:
        json.dump(overrides, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(json.dumps({k: v for k, v in report.items() if k != "changes"}, indent=2), file=sys.stderr)
    print(f"{len(changed)} override(s) -> {args.overrides}; report -> {args.report}. "
          f"Re-run stage 2 with --overrides to apply.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
