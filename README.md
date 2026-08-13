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
- [x] E098 production archive landed — per-track audio, Audition session, ElevenLabs Scribe ASR
- [x] Stage 2 rerun → `transcript.v1.md` + `segments.v1.jsonl`, 452 turns, both speakers named.
      Supersedes v0. Attribution is still `inferred` — see below.
- [ ] Earn `confirmed` attribution from the per-track audio, or decide diarization is enough
- [ ] Beat segmentation
- [ ] Research pass
- [ ] Character sheets for adam + tbj
- [ ] Fallback renderer
- [ ] Deploy

## On `inferred` vs `confirmed`

Speaker attribution in v1 comes from a diarization model, mapped to people by five
self-identifying anchors in the transcript. The mapping is evidenced; the turn boundaries are
still a model's guess, so `speaker_confidence` stays `inferred` per the spec's own definition.

The hand-labelled `speakers.md` in the archive agrees on all 452 turns — but it was produced from
the same diarization pass, so it corroborates nothing. Only the per-track audio can upgrade this.

## Ground rules

Nothing is generated at read time. Every tendril URL is fetched and must return 200 at build time.
Consent gates image generation and guests default to no likeness. The runner never holds a deploy key.
