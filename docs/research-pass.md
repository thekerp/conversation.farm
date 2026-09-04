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

   **This is a test on each item, not a ban on a question type.** The rule kills a link whose *only*
   justification is the mention. The strong `identify` is the exact inverse: the hosts describe
   something at length and never name it, so the reader cannot look it up at all. E098's hosts
   define copyleft and permissive licensing precisely, and never say GPL, MIT, BSD, Apache or
   copyleft; they discuss Heartbleed without once saying OpenSSL. Naming those is discovery, not a
   show note. Applying rule 2 at the type level instead of the item level cut all of them from the
   first E098 queue, and nothing in the artifact recorded that it had happened — which is why §9
   exists.
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

Recorded 2020-08-22, published 2020-09-10. Queue generated from the actual segmented audio.
Timestamps below are master-timeline seconds from `segments.v1.jsonl`, which is the timeline every
published timestamp must use.

| # | Type | Beat | Question |
|---|---|---|---|
| 1 | `verify` | 09:15 | "Tesla has open sourced all of their patents." True as stated? |
| 2 | `verify` | 34:52 | Git was written by Linus Torvalds, who also created Linux. |
| 3 | `since` | 21:26 | They contrast Apple's closed App Store with Android's openness. What's changed since 2020? |
| 4 | `since` | 45:33 | "Almost everything has an open source counterpart." Does that still hold in 2026? |
| 5 | `contradict` | 38:12 | Adam's claim that Git's append-only model should be rolled out to every other domain — strongest objection? |
| 6 | `enrich` | 34:52 | Best account of why Git was written, beyond the Torvalds trivia. |
| 7 | `since` | 52:41 | The blockchain-adjacent aside. What happened to that thesis? |
| 8 | `identify` | 20:41 | The specific licenses they gesture at without naming. |

Three of eight are `since`, which is the right shape for a six-year-old convo.

> Item 8 was written as `00:00`. The published episode opens with a cold open lifted from **20:41**
> and *moved* there, so `00:00` addresses audio from twenty minutes into the conversation. Any queue
> item generated from a timestamp has to be checked against `source.json` -> `structure`, or `since`
> questions get asked about the wrong moment.

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

---

## 8. Entity boxes

The named things — Heartbleed, Git, Torvalds, the App Store, Tesla — are the wrong shape for a
tendril and the right shape for a box. An `identify` on a thing they *said* produces a Wikipedia
link, which is the four-link baseline this project exists to beat, and rule 5 would cap a dozen of
them at one anyway. So they stop being tendrils and become their own class: a stored summary, a
link out, and no research budget spent.

**What they are:** orientation. A reader who doesn't know what Heartbleed was needs one sentence,
not a research finding. **What they are not:** discovery. That is what tendrils are for.

| | Tendril | Entity box |
|---|---|---|
| Job | take the reader somewhere the episode didn't | let the reader follow the episode at all |
| Earned by | a research job | being said on tape |
| Rule 3 cap (3/beat) | counts | exempt |
| Rule 5 one-domain | counts | exempt |
| Produced in | 4b | fetched after Gate 1, stored |

Rules:

1. **The term must be SAID on tape**, verbatim, and the record carries `said_as` proving it. A thing
   described but never named is an `identify` question — see rule 2 above. This is the line that
   keeps the box from swallowing the interesting half of the work, and `stage4a_verify_queue.py`
   enforces it against the transcript.
2. **Fetched and stored at production time.** Non-negotiable 1. A box that calls an API to render
   is a broken box.
3. **Every URL returns 200 at build time**, same as a tendril.
4. **Attribution and licence ship with the extract.** Wikipedia text is CC BY-SA; the credit line
   and the link back are not the renderer's option.
5. **A human picks which ship.** 4a proposes; proposing twelve is not shipping twelve. The cost is
   reader clutter, not bytes — default cap is six.

---

## 9. The decision ledger

A queue that lists only its survivors cannot be audited. The first E098 queue shipped twelve
questions and one prose sentence asserting that every `identify` and `enrich` candidate had failed
rule 2. The sentence was wrong, and there was no way to discover that except by asking the model to
re-derive its own reasoning from scratch.

So every candidate gets a fate, and the fate is data.

| Fate | Means |
|---|---|
| `queued` | in the queue |
| `folded` | absorbed into another item's scope or guards; `into` names it |
| `held` | deliberately parked with a reason, expected to return |
| `rejected` | cut by 4a, with the rule that cut it |
| `bounced` | cut by a **human** at a gate, with the stage that cut it |

`bounced` is the one that matters most and is the one §4's `human` block already half-captures.
§4 calls that block a training set: after ten convos we learn which question types we keep and
which we always cut. But the human's cuts are the smaller half of the funnel. Most candidates die
inside 4a, before anyone sees them. A training set blind to that half learns the wrong lesson.

**Reason codes are an enum, not prose.** Prose does not aggregate, and these decisions are meant to
flow to a review UI, where the whole point is filtering and counting: how often does
`rule3-attention-cap` fire, which beats keep losing candidates to `budget`, does
`promoted-to-entity` correlate with boxes nobody clicks. Prose reasons ride alongside for the human
reading one row; the code is what the interface sorts on.

Current codes: `rule2-mention-only`, `rule3-attention-cap`, `rule7-non-assertion`, `budget`,
`covered-by`, `promoted-to-entity`, `self-promotion`, `out-of-scope-stage`,
`timeline-unaddressable`, `gate1-cut`, `gate2-cut`.

A note on `self-promotion`: a host's own company is a legitimate *subject* of research and never a
legitimate tendril. The link a reader cannot audit as editorial is the one that contaminates the
links around it. If one ever ships, it ships with a disclosure label.

---

## 10. Gleanings — what the harvest left

`harvest` is the verb; a gleaning is what stays in the field after it. These are the places the
conversation came up to something and did not close on it.

It is its own block because it is none of the others. A check says they were wrong. A tendril goes
somewhere they didn't. A seed asks a question for a future convo. An entity explains a thing they
named. A gleaning is an observation about *this* conversation: the thing was in hand and was not
taken.

| Kind | Means | E098 |
|---|---|---|
| `unnamed` | described precisely, never named | Adam defines copyleft whole at 14:12 and never says the word; Brian defines permissive licensing at 19:11; the library behind Heartbleed is never named at all |
| `dropped` | raised, then abandoned | the popularity/path-dependence thread, left mid-sentence at 29:56 |
| `implied` | one step from what they said, untaken | — |
| `cut` | reached in the room, removed by the edit | Adam's *"so that, that should exist at the same time"* — a thought he then loses on tape, in material the edit deleted |

That last row is the one no other pipeline can produce. It exists only because stage 2b transcribes
what the edit removed.

Rules:

1. **Evidence or it does not ship.** Every gleaning quotes the words that came close, verbatim,
   checked against the transcript or the cut material.
2. **The thing must have been in hand.** Described, raised, or one step away. "They failed to
   mention X" is cheap and infinite — that is criticism, and this is not a criticism block.
3. **For `unnamed`, the term must NOT appear in the transcript.** The exact inverse of the entity
   rule in §8, and the verifier enforces both, so no term can be filed as a box and a gleaning at
   once. A thing they said is orientation; a thing they didn't is a thread to pull.
4. **Capped at five.** Same scarcity logic as tendrils and seeds.
5. **Never on a joke or an aside.**

A gleaning may carry `resolved_by` naming the research item that supplies the missing name — and
may carry `null`, which is its own finding. A lost thought stays lost, and saying so is more honest
than pretending research can recover it.

---

## 11. The gates run in a UI

`tools/gate/serve.py` — stdlib, no build step, loopback only.

```
python3 tools/gate/serve.py convos/zengineering-098
```

**The queue file is the source of truth and the UI edits it.** Not a database, not an export: every
click writes `research-queue.v1.json` atomically and re-runs the verifier, so the interface cannot
leave the file in a state the stage would reject without showing you. Approving is blocked while
the verifier is red — approving past a red verifier is how a bad anchor reaches a paid research
job.

It renders as a Slack-style thread on purpose. §2's protocol is reactions on a numbered message, so
the simulation exercises that shape — including the ✍️ add-a-question path, which §2 calls the
highest-leverage sixty seconds in the pipeline — before anyone builds the real integration. What it
teaches about the protocol is meant to feed back into `docs/slack-protocol.md`, which is still a
draft with 22 blocking holes.

Decisions land as a `human` block on each item, mirrored into `decisions.bounced` with reason code
`gate1-cut`. Nothing is deleted: a cut question stays in the file, stops counting against budget,
and stops being structurally validated, because its defects are usually why it was cut.
