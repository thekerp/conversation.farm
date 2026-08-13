#!/usr/bin/env python3
"""Stage 2b — transcribe what the edit removed.

A published episode is an edit. The material the hosts cut is not in any
transcript of the master, but it is sitting in the raw per-speaker tracks, and
some of it is the best thing in the episode. This stage reads the edit map from
`source.json`, extracts each cut window from each speaker's track, transcribes
them independently, and merges by timestamp.

Speaker attribution here is exact — it comes from track ownership, not a model.

Idempotent: output is written whole. Requires ffmpeg and whisper.cpp's
`whisper-cli` on PATH.

    python3 skill/stages/stage2b_cut_material.py \
        --convo convos/zengineering-098 \
        --model ~/whisper-models/ggml-small.en.bin

Timestamps in the output are final-mix / raw-track seconds. They are NOT master
timestamps — the master does not address this material at all.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

NOISE = {"[BLANK_AUDIO]", "(upbeat music)", "[ Silence ]", "[SILENCE]", ""}


def mmss(t: float) -> str:
    return f"{int(t) // 60:02d}:{int(t) % 60:02d}"


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{r.stderr[-2000:]}")


def transcribe_window(
    track: str, start: float, dur: float, model: str, frame_shift: float, workdir: str, tag: str
) -> list[tuple[float, str]]:
    """Extract one window from one track and transcribe it."""
    wav = os.path.join(workdir, f"{tag}.wav")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start - frame_shift:.3f}", "-t", f"{dur:.3f}",
         "-i", track, "-ac", "1", "-ar", "16000", wav])
    stem = os.path.join(workdir, tag)
    run(["whisper-cli", "-m", model, "-f", wav, "-oj", "-of", stem, "-np", "-nt"])
    with open(stem + ".json", encoding="utf-8") as fh:
        doc = json.load(fh)
    out = []
    for seg in doc.get("transcription", []):
        text = seg["text"].strip()
        if text not in NOISE:
            out.append((start + seg["offsets"]["from"] / 1000.0, text))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--convo", required=True, help="convo directory containing source.json")
    p.add_argument("--model", required=True, help="whisper.cpp ggml model")
    p.add_argument("--kinds", default="internal", help="comma-separated cut kinds to transcribe")
    p.add_argument("--out", default="cut-material.v1.json")
    args = p.parse_args()

    with open(os.path.join(args.convo, "source.json"), encoding="utf-8") as fh:
        src = json.load(fh)

    emap = src["edit_map"]
    frame_shift = 0.0784  # .sesx sample positions -> ffmpeg decode frame of the final mix
    tracks = {
        person: os.path.join(args.convo, src["tracks"][person])
        for person in src["participants"]
        if src["tracks"].get(person)
    }
    for person, path in tracks.items():
        if not os.path.exists(path):
            p.error(f"track missing for {person}: {path}")

    wanted = {k.strip() for k in args.kinds.split(",")}
    cuts = [c for c in emap["cuts"] if c["kind"] in wanted]

    results = []
    with tempfile.TemporaryDirectory() as work:
        for i, cut in enumerate(cuts, 1):
            a, b = cut["mix"]
            rows = []
            for person, path in tracks.items():
                for t, text in transcribe_window(
                    path, a, b - a, os.path.expanduser(args.model), frame_shift, work, f"c{i}_{person}"
                ):
                    rows.append({"t": round(t, 2), "speaker": person, "text": text})
            rows.sort(key=lambda r: (r["t"], r["speaker"]))
            results.append(
                {
                    "cut": i,
                    "mix": [a, b],
                    "seconds": round(b - a, 3),
                    "at": mmss(a),
                    "kind": cut["kind"],
                    "note": cut.get("note"),
                    "lines": rows,
                }
            )
            print(f"cut {i} [{mmss(a)}] {b - a:6.1f}s -> {len(rows)} line(s)", file=sys.stderr)

    doc = {
        "convo": src["id"],
        "timeline": "final-mix / raw-track seconds. NOT master seconds — the master does not "
                    "address this material.",
        "asr": "whisper.cpp small.en, one pass per isolated track",
        "speaker_confidence": "confirmed",
        "speaker_confidence_method": "Track ownership. Each window is transcribed from one "
                                     "speaker's isolated track; no diarization is involved.",
        "total_seconds": round(sum(r["seconds"] for r in results), 3),
        "cuts": results,
    }
    out = os.path.join(args.convo, args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {out} ({doc['total_seconds']} s across {len(results)} cuts)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
