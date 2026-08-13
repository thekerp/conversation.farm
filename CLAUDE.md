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

`convos/zengineering-098/` is the v1 target. It has a mono transcript (`transcript.v0.md`) produced
before per-track audio was available. **Per-track audio exists for the back catalog** — when the
tracks for 098 land, re-run stage 2 against them and supersede v0.
