# conversation.farm — Convo v1

**Status:** draft spec, 2026-08-13
**Owners:** Adam Kerpelman, T. Brian Jones
**Scope:** one back-catalog Zengineering convo, processed end to end, published at a real URL.

---

## 0. What this is

A pipeline that takes one recorded conversation and produces one page worth sending to a friend.

Not a platform. Not a network. Not an app. One page, one URL, one episode — built so that the
*second* one costs almost nothing.

The three decisions this spec is built on:

1. **v1 processes one old episode** you already know is good. New episodes come after the machine works.
2. **The checks block is public.** We fact-check ourselves on the page, at full strength.
3. **The renderer is Brian's call.** So the spec defines the data contract, not the front end, and
   ships a throwaway renderer so nothing blocks on that decision.

---

## 1. The unit: a convo

One recorded conversation → one convo → one page at `conversation.farm/zengineering/<number>`.

**Vocabulary rule: `convo` is the noun, `harvest` is the verb.** A convo is the durable object. To
harvest one is to run it through the pipeline and put a page on it. Nothing is ever "a harvest," and
the farm beds on the landing page — seed, plot, harvest, compost — stay as stage names describing
what's being done to a convo, which is what they always were.

This matters more than a naming preference. A convo isn't the *output* of the pipeline, it's the
thing that persists and accumulates: recorded, then segmented, then researched, then published, then
composted into later ones. Same object throughout, gaining fields. That's what makes it addressable
later, when somebody wants to graft one onto a topic of their own.

Scroll order:

| Block | Contents | Job |
|---|---|---|
| **Hook** | One sentence naming what got argued | Someone decides in four seconds whether to keep scrolling |
| **Spine** | 5–9 beats, in order: timestamp, the claim in one sentence, an audio clip | The hour, skimmable in ninety seconds |
| **Tendrils** | Per beat: researched link-outs — the paper, the person, the prior art, the counterargument | The differentiator. Show notes list what was mentioned; tendrils give you somewhere to go. |
| **Checks** | Where we were wrong, contested, or out of date — with sources | The reason it gets forwarded |
| **Seeds** | The questions the conversation didn't close | Somewhere to go that isn't "subscribe" |
| **Dirt** | Full transcript (collapsed), audio player, RSS link | The podcast ships unchanged |

---

## 2. The object

Every convo is a `convo.json` before it's a page. Beats, tendrils, checks, and seeds are typed
objects with stable IDs, because an addressable beat is what makes compost a query instead of a
memory. "This 2019 conversation argued the opposite of last week's" should be a lookup, not something
one of us happens to remember at the right moment.

```json
{
  "schema": "convo/1",
  "id": "zengineering-102",
  "farm": "zengineering",
  "number": 102,
  "slug": "welcome-to-zengineering",
  "title": "Welcome to Zengineering",
  "hook": "One sentence. What got argued, not what it was about.",
  "state": "recorded|transcribed|segmented|researched|reviewed|published|composted",
  "recorded": "2026-03-04",
  "published": null,
  "runtime_seconds": 3183,
  "participants": [
    { "name": "Adam Kerpelman", "role": "host" },
    { "name": "T. Brian Jones", "role": "host" }
  ],
  "media": {
    "audio_url": "https://…",
    "transcript": "transcript.md",
    "clips_dir": "clips/"
  },
  "beats": [
    {
      "id": "b3",
      "t": 328,
      "t_end": 412,
      "speaker": "tbj",
      "speaker_confidence": "inferred",
      "claim": "The claim in one sentence, in their words where possible.",
      "context": "Two or three sentences of what surrounds it.",
      "clip": "clips/b3.mp3",
      "tendrils": ["t7", "t8"],
      "checks": ["c2"]
    }
  ],
  "tendrils": [
    {
      "id": "t7",
      "beat": "b3",
      "kind": "paper|article|video|person|tool|prior_episode",
      "title": "",
      "url": "",
      "source": "",
      "why": "One line on why this is here. Never a summary of the link.",
      "retrieved": "2026-08-13"
    }
  ],
  "checks": [
    {
      "id": "c2",
      "beat": "b3",
      "verdict": "confirmed|off|wrong|contested|unverified|outdated",
      "claim_as_said": "",
      "what_we_found": "",
      "sources": ["t9"],
      "confidence": "high|medium|low",
      "host_note": null
    }
  ],
  "seeds": [
    { "id": "s1", "from_beat": "b7", "question": "" }
  ],
  "compost": [
    {
      "convo": "zengineering-064",
      "beat": "b2",
      "relation": "contradicts|extends|repeats|answers",
      "note": ""
    }
  ],
  "provenance": {
    "transcriber": "faster-whisper small.en, int8, chunked, VAD",
    "diarization": "none — mono mixed source; speakers content-inferred",
    "research_pass": "",
    "human_review": ["adam", "tbj"],
    "generated": "2026-08-13T00:00:00Z"
  }
}
```

**Why `provenance` is not optional.** We're publishing a block that says where we were wrong. That
only works if the reader can see how the machine reached that conclusion, and where it's shaky.
Publish the confidence, publish the method, publish the fact that speaker labels are guesses.

---

## 3. The checks block

The spiciest part of the page, so it gets the most rules.

**Verdicts:**

| Verdict | Means |
|---|---|
| `confirmed` | We said it, it holds up. Sourced. |
| `off` | Directionally right, details wrong |
| `wrong` | Factually incorrect |
| `contested` | No consensus; here are both sides |
| `unverified` | Couldn't confirm either way, and we're saying so |
| `outdated` | True when we said it, not anymore |

`confirmed` matters as much as `wrong`. A block that only ever flogs us is performance, and after two
episodes we'd start avoiding claims to keep the page clean. Verified-correct entries keep it honest
and keep it usable.

**Editorial rules:**

1. Check claims of fact. Never check a joke, an opinion, a prediction, or a preference.
2. Every check carries at least one source, and the source is a tendril object, not a bare URL.
3. Low confidence gets said out loud in the entry, not buried in provenance.
4. `host_note` is a right of reply. Either of us can respond inline, and the response ships with it.
5. Guests get checked by the same standard as hosts, and get a right of reply before publication.

That last one is a real editorial commitment. Worth deciding now whether guests are told about the
checks block *before* they record, because I think the answer is yes and it changes the pitch email.

---

## 4. Pipeline

| # | Stage | Who | Notes |
|---|---|---|---|
| 1 | Drop the recording | Human | Folder or Slack channel; filename carries the episode number |
| 2 | Transcribe | Auto | Chunked local Whisper. ~25 min compute per hour of audio on one core. Proven. |
| 3 | Segment into beats | Auto | 5–9 beats. Long conversations don't get more beats, they get better ones. |
| 4 | Research pass | Auto | Per beat: search, fetch, verify. Drafts tendrils and checks. The only hard part. |
| 5 | Assemble `convo.json` | Auto | Schema-validated or it fails loudly |
| 6 | **Review gate** | Human | Slack ping-pong. Approve, rewrite, or kill beats and checks. |
| 7 | Cut clips | Auto | ffmpeg, per beat, from the beat timestamps |
| 8 | Render + commit | Auto | Renderer reads `convo.json`, writes a page |
| 9 | **Publish gate** | Human | Deploy |
| 10 | Audio to Transistor | Human | Unchanged from today |

Two human gates. Everything between them runs unattended.

**Stage 4 is the whole product.** If the research pass produces tendrils that are just the Wikipedia
article for every proper noun, there's no product here and we should go back to minimum viable
podcast. Budget the effort accordingly.

---

## 5. Renderer contract

The pipeline never imports the renderer. Input is `convo.json` + `transcript.md` + a clips
directory; output is a page. That's the entire interface.

- **Fallback renderer** ships with v1: one script, no framework, no build step, writes static HTML
  using the landing page's tokens. Exists so nothing waits on a front-end decision.
- **Brian's renderer** replaces it whenever he wants, without touching stages 1–7.
- If both exist, the fallback stays in the repo as the reference implementation.

---

## 6. Definition of done for v1

- [ ] 5–9 beats, each with a real timestamp and a working clip
- [ ] ≥2 tendrils per beat, and at least one per beat that isn't the obvious first search result
- [ ] ≥3 checks, including at least one non-`confirmed` verdict if the material supports one
- [ ] 1–3 seeds
- [ ] **Zero fabricated URLs.** Every tendril fetched and confirmed live at build time. A dead link
      is a bug that fails the build.
- [ ] Provenance block complete and honest
- [ ] Page loads with no JS required to read it
- [ ] Live at `conversation.farm/zengineering/<number>`
- [ ] Sent into one real group text. Someone who isn't us does something with it.

That last line is the actual test. Everything above it is scaffolding.

---

## 7. Non-goals for v1

Accounts. Comments. Upvotes, forever. Search. The network. Grafting. Seed exchange. Video. Any farm
but Zengineering. Batch processing the back catalog. A CMS. Anything with a login.

---

## 8. Illustrative example

Beats drawn from the 2026-08-12 Adam/Brian call, because it's the transcript we have in hand. Tendril
URLs are deliberately empty — the spec's own quality bar forbids unfetched links, and a spec that
fakes them teaches the agent to fake them.

```json
{
  "beats": [
    {
      "id": "b1", "t": 328, "speaker": "adam", "speaker_confidence": "inferred",
      "claim": "Podcasting isn't a novel publishing form anymore, so the only remaining reasons to do it are the conversation itself and the professional cover it provides.",
      "tendrils": ["t1", "t2"], "checks": []
    },
    {
      "id": "b3", "t": 814, "speaker": "tbj", "speaker_confidence": "inferred",
      "claim": "Token cost trends toward raw energy cost, which removes the need for algorithmic curation — an LLM can read every candidate item per user instead.",
      "tendrils": ["t5", "t6"], "checks": ["c1"]
    },
    {
      "id": "b5", "t": 1785, "speaker": "tbj", "speaker_confidence": "inferred",
      "claim": "Prior social networks were architected around structured databases; nobody has built one on LLMs and vector search yet.",
      "tendrils": ["t8", "t9"], "checks": ["c2"]
    },
    {
      "id": "b7", "t": 2130, "speaker": "tbj", "speaker_confidence": "inferred",
      "claim": "Conversation is the foundational interface. Everyone has a podcast because talking to people you like is fun, and the RSS feed is incidental to that.",
      "tendrils": ["t11"], "checks": []
    }
  ],
  "checks": [
    {
      "id": "c1", "beat": "b3", "verdict": "contested",
      "claim_as_said": "Inference cost goes to the cost of energy.",
      "what_we_found": "Directionally supported by observed price-per-token declines; contested on the timeline and on whether frontier-model inference follows the same curve as small-model inference.",
      "sources": ["t5", "t6"], "confidence": "medium", "host_note": null
    }
  ],
  "seeds": [
    { "id": "s1", "from_beat": "b5", "question": "What does a social graph look like when the edges are semantic rather than declared?" }
  ]
}
```

---

## 9. Speaker attribution — solved by per-track audio

Per-participant tracks exist for the back catalog, which removes the need for any diarization model.

**Stage 2 takes a directory of tracks, not a file.** One file per speaker, named by person id
(`tracks/adam.wav`, `tracks/tbj.wav`). Each is transcribed independently, segments are merged and
sorted by timestamp, and the speaker is whoever owns the track. Attribution is exact and
`speaker_confidence` is `confirmed`.

Two details that will bite:

- **Bleed.** Each track picks up the other person. Keep a segment only on the track where that
  speaker's energy is highest across the overlapping window, or you get every line twice.
- **Drift.** Separately recorded tracks drift over an hour. Cross-correlate the first sixty seconds
  to align, re-check at the end, fail loudly past 200 ms.

Mono is the fallback. When only a mixed file exists, mark every speaker `inferred` and say so in
provenance. `convos/zengineering-098/transcript.v0.md` is a mono transcript and carries that flag.

**Riverside's transcript is the bedrock reference, not the source of truth.** Keep it and diff ours
against it. When our pipeline agrees within tolerance across several convos, we've earned the right
to stop depending on it.

## 10. Open, not blocking

1. Where do clips get hosted, and do we need video for v1 or is audio enough
2. URL structure once there's a second farm — `conversation.farm/<farm>/<n>` or a subdomain
3. Who owns the repo, and does it go public before or after the first convo ships
4. Do guests get told about the checks block in the pitch email (I think yes)
5. Whether the fallback renderer is the one that ends up shipping anyway

---

## 11. Next up

1. **Pick the episode.** The only blocking input. Criteria: it has claims of fact in it, it has
   people and papers and events worth chasing, you both remember it fondly, and it isn't pegged to
   news that's since moved. Something evergreen you'd still defend.
2. Run stages 1–5 against it in a recorded public working session.
3. Fight about the beats at the review gate on camera, because that's the episode.
