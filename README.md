# conversation.farm

A pipeline that turns one recorded conversation into one fast, media-rich page.

We farm conversations. Not content.

The atomic unit is a **convo**: recorded, transcribed, segmented into beats, researched, reviewed,
published, and eventually composted into later ones. Same object throughout, gaining fields.
`convo` is the noun. `harvest` is the verb.

## Read in this order

| Doc | What's in it |
|---|---|
| [`docs/convo-v1-spec.md`](docs/convo-v1-spec.md) | The unit, the object, the pipeline, the checks block, definition of done |
| [`docs/tech-stack.md`](docs/tech-stack.md) | Three planes, performance budget, characters and consent, the production skill |
| [`docs/research-pass.md`](docs/research-pass.md) | Stage 4 — the queue, the Slack loop, the anti-slop rules |
| [`CLAUDE.md`](CLAUDE.md) | How agents should work in here |

## v1

One back-catalog convo, end to end, live at a real URL.

**Target:** `convos/zengineering-098` — "On Open Source Collaboration," recorded 2020-09-10.
Its current show notes are four links. That's the bar.

## Status

- [x] Landing page drafted (`site/index.html`)
- [x] Spec, tech stack, research pass drafted
- [x] E098 audio pulled, mono transcript produced (`transcript.v0.md`, 11k words)
- [ ] Per-track audio for E098 → re-run stage 2, supersede v0
- [ ] Beat segmentation
- [ ] Research pass
- [ ] Character sheets for adam + tbj
- [ ] Fallback renderer
- [ ] Deploy

## Ground rules

Nothing is generated at read time. Every tendril URL is fetched and must return 200 at build time.
Consent gates image generation and guests default to no likeness. The runner never holds a deploy key.
