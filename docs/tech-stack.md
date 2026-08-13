# conversation.farm — Tech stack & the production skill

**Addendum to:** `convo_v1_spec.md`
**Status:** draft, 2026-08-13

---

## 0. Three planes, kept apart

| Plane | What it is | Runtime |
|---|---|---|
| **Reader** | The scrollable convo page | Static files on a CDN. No server, no framework, no runtime. |
| **Data** | `convo.json`, transcripts, clips, images, people | Git. The repo is the database. |
| **Producer** | The skill Adam and Brian install, plus a Slack channel | Runs on our machines, on demand. Never in the reader's path. |

The separation is the performance strategy. Every expensive thing — transcription, research,
image generation, rendering — happens in the producer plane, at production time, once. The reader
gets bytes that were finished hours earlier.

**Nothing is generated at read time. Ever.** The moment a page calls a model to render itself, the
usability tenet is dead.

---

## 1. Reader plane

### Performance budget

Numbers, not vibes. A convo page that misses these doesn't ship.

| Metric | Budget |
|---|---|
| HTML, gzipped | ≤ 40 KB |
| Critical CSS, inlined in `<head>` | ≤ 14 KB (one round trip) |
| Deferred CSS | ≤ 30 KB |
| JavaScript, total | ≤ 25 KB gz, **zero render-blocking** |
| Fonts | 2 files max, subset to used glyphs, self-hosted, preloaded |
| Above-fold images | ≤ 150 KB |
| LCP, Slow 4G | ≤ 1.2 s |
| CLS | ≤ 0.02 |
| INP | ≤ 100 ms |
| Readable with JS disabled | Yes, entirely |

### How it's built

- **Static prerender at build time.** One HTML file per convo, committed. No SSR, no hydration, no
  client router on first view.
- **Self-hosted, subset fonts.** The landing page currently pulls Google Fonts over the network —
  that's a render-blocking third-party handshake and it comes out for convo pages. Subset Fraunces
  and Space Grotesk to the glyphs actually used, `font-display: swap`, preload only the weights above
  the fold.
- **`content-visibility: auto` on every beat section**, with `contain-intrinsic-size` set from the
  known block height. On a long scrollable page this is the single biggest win — the browser skips
  layout and paint for everything offscreen.
- **Scroll effects in CSS, not JS.** Scroll-driven animations (`animation-timeline: view()`) run off
  the main thread. Never attach a `scroll` listener. Fall back to `IntersectionObserver`, and gate
  everything behind `prefers-reduced-motion`.
  *Verify current Safari and Firefox support at build time — the fallback path is mandatory either way.*
- **View Transitions + speculation-rules prefetch** for convo-to-convo navigation, as progressive
  enhancement only.
- **JS is enhancement, full stop.** Clip playback, transcript expand, and the beat rail attach after
  first paint. The page reads fine without them.

### Media policy — the one place waiting is allowed

| Asset | Rule |
|---|---|
| Beat clips | Opus mono, ~32 kbps. A 15-second clip is ~60 KB. `preload="none"`, fetched on click. |
| Full episode audio | Linked, never preloaded |
| Images | AVIF with WebP fallback, explicit width/height, LQIP placeholder, `loading="lazy"` below fold, `fetchpriority="high"` on the hero only |
| Video | Poster frame always, `preload="none"`, click to play, never autoplay. **The only permitted wait.** |

**Per-convo byte budget: 2 MB for the whole page including all lazy media.** Rich media is what will
kill the performance tenet, and it'll kill it gradually, one nice-looking addition at a time. The
budget is the defense.

---

## 2. People and characters

A convo references people. People persist across convos and own their own likeness.

```json
{
  "schema": "person/1",
  "id": "adam",
  "name": "Adam Kerpelman",
  "handle": "kerp",
  "bio": "",
  "links": [],
  "character": {
    "sheet": "people/_characters/adam/sheet.md",
    "refs": ["people/_characters/adam/ref/01.png", "…"],
    "invariants": ["glasses", "beard", "specific palette lock"],
    "seed": 88214,
    "negative": ["photorealism", "extra fingers"],
    "approved_styles": ["riso", "woodcut", "8bit"],
    "consent": { "generative": true, "updated": "2026-08-13" }
  }
}
```

### How consistency actually works

Consistent characters across styles is not a prompt problem, it's a **reference-set** problem. Three
things have to be locked:

1. **A written character sheet** — invariant tokens that must never drift. Not a vibe, a checklist.
2. **Three to five canonical reference renders** that the generator gets as image input every time.
3. **A fixed seed per person per style.**

Style is chosen **per convo, not per person**, so both people in a convo appear in the same world.
One convo, one visual language.

### Generation happens at production time

Character renders are produced once, per person per style, committed as static AVIF, and reused
across every convo in that style. A convo page never generates an image. Adding a new style is a
producer-plane job that touches the person's directory, not the pages.

### Consent is not a setting, it's a gate

- A person owns their character sheet. It lives in their own directory.
- **A new style requires that person's explicit approval** before it's generated or published.
- **Guests are opt-in and default to no likeness.** Absent consent and approved references, a guest
  gets a typographic card — initials, name, role — and it looks deliberate, not broken. Generating a
  real person's cartoon likeness because they came on a podcast is not a thing we do.
- `consent.generative: false` is honored everywhere in the pipeline, with no override flag.

### Generation, v0

Start with the OpenAI image API and don't build an abstraction layer until there's a second provider
to abstract over.

- **Character renders.** Reference images plus the character sheet go in as image input; a fixed
  prompt template and a fixed per-person seed go with them. Produced once per person per style,
  committed as AVIF, reused across every convo in that style.
- **Beat art.** One hero plus three to five beat images per convo, all in the convo's chosen style,
  with the two characters composited from their locked renders rather than re-generated per beat.
- **Sidecar provenance, always.** Every generated image gets a JSON sidecar: prompt, model, seed,
  reference images, operator, date. Non-negotiable on a page whose premise is showing our work.
- **Cost and runtime go in the convo's provenance block** like every other model call.

Generation runs on the producer plane, at production time, once. If an image is missing at build
time the page ships without it rather than waiting.

### v1 scope

One style. Two people. Both of you, both consenting, both with real reference sets. Multi-style
switching is the demo for v2 — it's the least reliable part of the whole stack and it cannot be
allowed to block the first convo shipping.

---

## 3. The production skill

One skill. Both of you install the same one. No "Adam's version."

### What it is

A Claude skill wrapping the ten pipeline stages from `convo_v1_spec.md` §4, with two properties that
make two-person operation work:

- **Git is the truth. Slack is the interface.** Every decision lands as a commit. Slack is where the
  decision gets made, not where it lives.
- **Every stage is idempotent.** Re-running stage 4 produces the same output, overwrites cleanly, and
  never appends duplicates. Output is keyed by stage, so a re-run is safe from any state.

### The Slack protocol

Channel `#convo-farm`. One thread per convo, opened by whoever drops the recording.

The skill posts each beat as its own message in the thread, so reactions attach per beat. Decisions
are emoji, because typing a paragraph to approve a beat is how a review gate dies:

| Reaction | Means |
|---|---|
| ✅ | Approve this beat as written |
| ✂️ | Cut it |
| 🔁 | Redo — the skill reads your reply for what to change |
| 🔎 | Tendrils are weak, research this one harder |
| ⚠️ | This check is unfair or wrong, pull it |
| 🔒 | Locked, ready for publish gate |

The skill reads the thread, applies the decisions, commits, and posts a diff summary. Either of you
can run it. Neither of you has to be the one who ran it last.

### Concurrency

Two people running the same skill against the same convo is the obvious failure mode.

- **A branch per convo** is the durable lock: `convo/zengineering-102`.
- **A claim message in the thread** before any stage starts, with the stage name and the operator.
  The skill checks for an unresolved claim and refuses rather than racing.
- **Claims expire** after 30 minutes so a crashed run doesn't wedge the convo.
- Merge to `main` is what publishes. That's the publish gate, and it's a PR.

### Secrets

Neither machine holds a deploy key. The skill opens PRs; CI deploys on merge. Model API keys stay
local to each operator. Slack token is per-user, not a shared bot credential.

---

## 4. Repo layout

```
conversation.farm/
  site/                     landing page, shared tokens
  tokens.css                one source of truth for color and type
  people/
    adam.json
    tbj.json
    _characters/
      adam/{sheet.md, ref/, styles/riso/}
  convos/
    zengineering-102/
      convo.json
      transcript.md
      clips/
      images/
      index.html            built, committed
  renderers/
    fallback/               python, no deps, reference implementation
  skill/
    SKILL.md
    stages/
```

Design tokens live in exactly one file, shared by the landing page, the fallback renderer, and
whatever Brian builds. A convo page and the front door should be visibly the same property.

---

## 5. Deferred, deliberately

Search. Accounts. Comments. Multi-style character switching. Video generation. Real-time anything.
A CMS. Any read path that hits a database. More than one farm.

---

## 6. Risks worth naming

1. **Media budget creep.** Every individual addition will look reasonable. The 2 MB cap is the only
   thing standing between this and a page that takes six seconds to become useful.
2. **Character consistency is the flakiest component in the stack.** Ship one style, prove the
   reference-set approach holds across two convos, then expand.
3. **Slack-as-interface works beautifully for two people and badly for six.** Fine for v1; it's a
   known replacement, not a permanent choice.
4. **Committing built HTML and binary media to git will bloat the repo.** Watch it from convo one;
   the answer is probably media on object storage with the repo holding pointers, but not yet.
5. **Scroll-driven CSS support varies.** The IntersectionObserver fallback isn't optional, and the
   page has to be good with no motion at all.
