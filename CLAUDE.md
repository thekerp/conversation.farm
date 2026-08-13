# CLAUDE.md

Working instructions for agents in this repo. Read this before touching anything.

## What this is

A pipeline that turns one recorded conversation into one fast, media-rich page.
The atomic unit is a **convo**. `convo` is the noun; `harvest` is the verb.

Read `docs/convo-v1-spec.md` first, then `docs/tech-stack.md`, then `docs/research-pass.md`.

## Non-negotiables

1. **Nothing is generated at read time.** Transcription, research, image generation, and rendering
   all happen at production time. A page that calls a model to render itself is a broken page.
2. **The performance budget in `docs/tech-stack.md` §1 is a gate.** A convo page that misses it does
   not ship. 2 MB total including all lazy media.
3. **Every tendril URL is fetched and must return 200 at build time.** A dead link fails the build.
   Never write a URL you have not fetched. A fabricated citation on a page whose whole premise is
   self-fact-checking is the worst possible bug.
4. **Consent gates image generation.** `person.character.consent.generative: false` is honored
   everywhere, with no override flag. Guests default to no likeness.
5. **Every stage is idempotent.** Re-running a stage overwrites cleanly and never appends duplicates.
6. **The runner never holds a deploy key.** Agents open PRs. CI publishes on merge to `main`.

## Layout

```
docs/                 specs — the source of truth for intent
schemas/              convo.schema.json — validate before writing
site/                 landing page, shared design tokens
people/               person records and character sheets
convos/<farm>-<n>/    source metadata, transcript, segments, convo.json, clips, images
renderers/fallback/   reference renderer: python, no deps, no build step
skill/                the production skill both operators install
```

## Pipeline stages

Defined in `docs/convo-v1-spec.md` §4. Two human gates: beat review and publish. Everything else
runs unattended.

Stage 2 (transcribe) prefers **per-track audio** — one file per speaker. Transcribe each track
independently, merge segments by timestamp, and speaker attribution is exact with no ML. Only fall
back to mono when tracks don't exist, and mark `speaker_confidence: "inferred"` when you do.

## Working style

- Small commits, one stage per commit, message names the stage and the convo id.
- Branch per convo: `convo/<farm>-<number>`.
- Validate against `schemas/convo.schema.json` before writing `convo.json`. Fail loudly.
- Never edit a `convo.json` by hand in a way a stage can't reproduce.
- Record cost and runtime for every model call into the convo's provenance block.
- When something is inferred rather than confirmed, say so in the data, not just the commit message.

## Current state

`convos/zengineering-098/` is the v1 target. The full production archive landed on 2026-08-13 —
isolated per-speaker tracks, the Adobe Audition session, and an ElevenLabs Scribe pass with
word-level timings. Stages 1–3 are done. See `ROADMAP.md` for what is next and what is blocked.

What that archive changed, and what you must not re-derive:

- **A published master is an EDIT of the session.** E098's is 8 clips with 6 internal cuts, 87.1 s
  of conversation removed, and a cold open lifted from 20:41 and *moved* to the front. Master and
  session timelines diverge by up to 83.4 s and no single offset relates them. Every published
  timestamp is on the master timeline. The map is `source.json → edit_map`.
- **Attribution is `confirmed`,** earned from per-track audio ownership, not from the transcript.
  Stage 2c arbitrates every turn against the isolated tracks.
- **Never read a duration from `ffprobe format.duration`.** It reads 5.510 s short on E098's master.
- **Never derive timings from the archive `.srt`.** 37.8% of its cues are off by more than a second.
- **Scribe's `logprob` finds none of the entity errors.** Diffing against the older Whisper pass
  (`transcript.v0.md`) finds all of them. That is why v0 is retained despite being lossier — but it
  has a 600 s duplicated block at `segments.v0.jsonl` indices 850–1035 that readers must drop.
- **Corrections live in data, never in the transcript.** `corrections.json` holds music windows,
  the ASR lexicon, and misspoken referents; the stage applies them. When Adam says "Riot" he means
  Epic Games — that ships as an annotation and a check, not as a repair.

## Stages that exist

```
skill/stages/stage2_transcript.py         ASR -> transcript.v1.md + segments.v1.jsonl
skill/stages/stage2b_cut_material.py      transcribes what the edit removed, off the raw tracks
skill/stages/stage2c_arbitrate_speakers.py  per-track energy overrides the diarizer
```

Stage 2 is the only writer of the transcript. Stage 2c emits overrides that stage 2 consumes, so
re-running stage 2 cannot silently undo the arbitration. Every stage is idempotent — verify it by
running twice and diffing hashes.

## Verify before you ship

Anything generated — beats, claims, tendrils, checks — gets walked adversarially before it lands.
The first beat set failed all three passes with 39 findings, two of them quotes that changed meaning
when trimmed. On a page whose premise is self-fact-checking, that is the whole failure mode. Assume
your first draft has the same defects and go looking for them.
