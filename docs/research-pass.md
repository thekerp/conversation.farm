# The research pass

**Stage 4 of the convo pipeline. The only stage that makes this a product.**
Addendum to `convo-v1-spec.md` and `tech-stack.md`. Draft 2026-08-13.

---

## 0. What it does

In: a segmented convo — beats with claims, plus the full transcript.
Out: **tendrils** (where to go next) and **checks** (where we were wrong), each sourced.

Everything upstream of this is plumbing that's been solved for years. If the research pass produces
the Wikipedia page for every proper noun, there's no product here.

---

## 1. It's a queue of questions, not a prompt

The failure mode is handing a deep research model an hour-long transcript and saying "research this."
You get a book report. What we want is a small number of specific questions, each of which produces
one defensible artifact on the page.

So stage 4 splits in two:

| Sub-stage | Model | Job |
|---|---|---|
| **4a. Extract** | Cheap, fast | Read the transcript. Pull every proper noun, factual claim, number, date, and named work. Emit a **research queue** of typed questions. No searching. |
| **4b. Research** | Deep research model | Run the approved queue. One job per question. Multi-source, cited, slow. |

4a is cheap enough to re-run freely. 4b costs real money and real minutes, which is exactly why a
human approves the queue before it runs.

### Question types

| Type | Asks | Feeds |
|---|---|---|
| `identify` | Who or what is this thing they name in passing? | tendril |
| `enrich` | What's the best thing to read or watch next on this? | tendril |
| `verify` | Is this claim of fact true? | check |
| `contradict` | What's the strongest good-faith counterargument? | tendril |
| `since` | **What has changed about this since the recording date?** | check + tendril |

### `since` is the one that matters

It's the whole reason to start with the back catalog. E098 was recorded in September 2020. Six years
have happened to open source. Every `since` result is a thing no show notes page anywhere has, and it
gets *better* the older the convo is — which turns the archive from a liability into the asset.

It's also what makes compost work. A `since` result is the natural link between an old convo and a
new one.

**Rule: a `since` answer must cite at least one source published after the convo's recording date.**
Otherwise it's an `enrich` wearing a costume.

---

## 2. The Slack loop

Channel `#convo-farm`, one thread per convo. Two gates, because the expensive thing sits between them.

```
skill                            humans
  │
  ├─ posts research queue ──────► ✅ / ✂️ / ✍️ add a question / 🔝 prioritize
  │                                        │
  ◄────────────────────────────────────────┘
  │
  ├─ runs 4b on the cloud runner (minutes, async, nobody waits)
  │
  ├─ posts one message per result ─► ✅ tendril / ⚠️ make it a check
  │   (claim, finding, sources,      ✂️ drop / 🔁 rerun with a note
  │    confidence)                            │
  ◄─────────────────────────────────────────-─┘
  │
  └─ writes convo.json, opens PR
```

**Gate 1 — approve the questions.** The queue posts as one message, numbered. Cheap to read, cheap to
edit, and it's where either of us can add the question the machine wouldn't think to ask. This is the
highest-leverage sixty seconds in the whole pipeline.

**Gate 2 — approve the results.** One message per result so reactions attach per finding. A result
with thin sources or low confidence gets ✂️ without discussion.

Both gates are async. The skill never blocks waiting for a human, and a human never waits for a model.

---

## 3. Anti-slop rules

These are build-breaking, not guidelines.

1. **Every tendril URL is fetched at build time and must return 200.** A dead link fails the build.
2. **No tendril whose only justification is "they mentioned it."** That's a show note. A tendril earns
   its place by taking the reader somewhere the episode didn't.
3. **Maximum three tendrils per beat.** Scarcity is the quality signal. Twelve links is a search
   results page.
4. **At least one tendril per beat must be non-obvious** — not the Wikipedia article, not the first
   result.
5. **One tendril per domain per convo.** Forces source diversity.
6. **Every check carries a source and a confidence, both published.**
7. **No check on a joke, an opinion, a prediction, or a preference.** Claims of fact only.
8. **`unverified` is a real, publishable verdict.** Saying we couldn't confirm it beats guessing.

---

## 4. Output

Each queue item produces one `research_item`, which the assembler turns into tendrils and checks.

```json
{
  "id": "r07",
  "beat": "b4",
  "type": "verify",
  "question": "Did Tesla open source its patents?",
  "finding": "",
  "verdict": "confirmed|off|wrong|contested|unverified|outdated",
  "confidence": "high|medium|low",
  "sources": [
    { "title": "", "url": "", "publisher": "", "published": "", "retrieved": "2026-08-13" }
  ],
  "model": "",
  "cost_usd": 0.0,
  "runtime_s": 0,
  "human": { "decision": "tendril|check|dropped|rerun", "by": "adam", "note": "" }
}
```

The `human` block is not bookkeeping. It's the training set. After ten convos we'll know which
question types we keep and which we always cut, and 4a can start proposing a better queue.

---

## 5. Worked example — E098, from the real transcript

Recorded 2020-09-10. Queue generated from the actual segmented audio.

| # | Type | Beat | Question |
|---|---|---|---|
| 1 | `verify` | 09:01 | "Tesla has open sourced all of their patents." True as stated? |
| 2 | `verify` | 34:40 | Git was written by Linus Torvalds, who also created Linux. |
| 3 | `since` | 21:26 | They contrast Apple's closed App Store with Android's openness. What's changed since 2020? |
| 4 | `since` | 45:33 | "Almost everything has an open source counterpart." Does that still hold in 2026? |
| 5 | `contradict` | 38:12 | Adam's claim that Git's append-only model should be rolled out to every other domain — strongest objection? |
| 6 | `enrich` | 34:40 | Best account of why Git was written, beyond the Torvalds trivia. |
| 7 | `since` | 52:41 | The blockchain-adjacent aside. What happened to that thesis? |
| 8 | `identify` | 00:00 | The specific licenses they gesture at without naming. |

Three of eight are `since`, which is the right shape for a six-year-old convo.

**What I'd expect back, before running it:**

- **#1 → `off`.** Tesla made a patent pledge in 2014 — a conditional non-assertion, not an open source
  release, and the conditions have teeth. Directionally right, materially wrong. This is the best kind
  of check: the point they were making survives, the fact doesn't.
- **#2 → `confirmed`.** Cleanly true, well documented. Proves the block isn't only self-flagellation.
- **#4 → the money result.** In 2020 the trend line pointed one way. Since then a run of major projects
  moved off open source licenses, and separately open-weight AI models arrived and changed what the
  claim even means. The 2020 take is half-vindicated and half-inverted, which is far more interesting
  than either.
- **#3 → substantial.** Regulatory and litigation changes since 2020 have reshaped the exact
  distinction they drew.

None of that is in the current show notes, which are four links: Wikipedia, a Wired guide, a
Unix-vs-Linux SEO page, and a CIO listicle. That contrast is the demo.

---

## 6. Budget

| | Target |
|---|---|
| Queue size | 6–12 questions per convo |
| Deep research jobs | 1 per approved question |
| Wall clock, 4b | Minutes per job, run in parallel, async |
| Cost per convo | Track it from convo one. Report it in the thread. |
| Human time, both gates | Under 10 minutes combined |

If a human spends more than ten minutes per convo on research review, the extraction stage is bad and
that's the thing to fix — not the reviewer's patience.

---

## 7. Where it runs

4b wants a cloud runner. Requirements to hand Brian:

- Stateless. Clone, run one stage, push a branch, exit.
- ffmpeg, Python, enough cores that Whisper isn't the bottleneck — a GPU makes stage 2 disappear
- Outbound network for research; **no inbound**
- Holds a Slack token and model keys; **holds no deploy key**
- Publishing happens on merge to `main`, in CI, not on the runner

The runner can never publish. That's the whole security model, and it's one sentence.
