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

**Target:** `convos/zengineering-098` — "On Open Source Collaboration," recorded 2020-08-22,
published 2020-09-10.
Its current show notes are four links. That's the bar.

## Status

- [x] Landing page drafted (`site/index.html`)
- [x] Spec, tech stack, research pass drafted
- [x] E098 audio pulled, mono transcript produced (`transcript.v0.md`, 11k words)
- [x] E098 production archive landed — per-track audio, Audition session, ElevenLabs Scribe ASR
- [x] Stage 2 rerun → `transcript.v1.md` + `segments.v1.jsonl`, 451 turns, both speakers named.
      Supersedes v0.
- [x] `confirmed` attribution earned from the per-track audio (38 dB turn-level separation,
      19/19 blocks, wrong-offset controls at chance)
- [x] Master↔raw edit map recovered and verified — 8 clips, 6 internal cuts, 87.1 s of
      conversation cut, cold open lifted from 20:41
- [x] The 99 s the edit removed, transcribed off the isolated tracks (`cut-material.v1.md`)
- [x] Riverside transcript added as the bedrock reference; per-turn speaker arbitration against
      the per-track audio corrected 5 turns the diarizer got wrong
- [ ] Decide: beats from the released audio only, or clips cut from the raw tracks so the 87.1 s
      of cut conversation becomes addressable
- [ ] Music-bed licence answered before any page hosts master 0–33 s or 3634–3683 s
- [ ] Beat segmentation
- [ ] Research pass
- [ ] Character sheets for adam + tbj
- [ ] Fallback renderer
- [ ] Deploy

## What the archive turned out to be

The E098 archive is the whole production tree, not just audio. Isolated per-speaker tracks, the
Adobe Audition session, and an ElevenLabs Scribe pass with word-level timings. Auditing it moved
several things the specs assumed:

- **Attribution is `confirmed`**, earned the way the spec asks — per-track audio ownership, 38 dB
  median separation across 170 turns, with wrong-offset controls at chance. Not from the transcript.
- **The episode opens with a cold open lifted from 20:41** and *moved*, not copied. So the first
  turn of the transcript is out of chronological order, and a beat anchored at `t=0` is quoting a
  moment twenty minutes in.
- **The master is an 8-clip edit of the raw tracks**, with 87.1 s of conversation cut. Master and
  raw timelines differ by up to 83.4 s; a single offset between them is wrong everywhere.
- **`speakers.md` is not a human pass.** It is byte-reproducible from the Scribe JSON. It agrees
  with the diarization on all 451 turns and therefore corroborates nothing.
- **Three ASR passes now disagree usefully.** Scribe (canonical), faster-whisper v0, and
  Riverside. Two of the three write "Engineering Podcast" — only faster-whisper heard the show's
  own name. Riverside gets "DeFi" right where Scribe wrote "defy". Only Scribe has the Heartbleed
  passage at all.
- **Riverside is a text reference, not a speaker reference.** Its diarization puts the Epic/Apple
  exchange on the wrong host; the isolated tracks disagree with it by 10 dB. Joining it by
  timestamp also manufactures disagreements, because its block times lead their text — join by text.
- **Scribe's `logprob` cannot find the errors that matter** — median −3.6e-07, and it flags none of
  the five entity problems. Diffing against the older Whisper pass found all of them with no audio.
  That is why `transcript.v0.md` is kept despite being lossier.

Everything measured is in `convos/zengineering-098/source.json`. Known ASR errors and misspoken
referents live in `corrections.json` and are applied by the stage, never by hand.

## Ground rules

Nothing is generated at read time. Every tendril URL is fetched and must return 200 at build time.
Consent gates image generation and guests default to no likeness. The runner never holds a deploy key.
