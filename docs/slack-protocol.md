# The harvest thread — Slack protocol

**Addendum to:** `convo-v1-spec.md` §4, `tech-stack.md` §3, `research-pass.md` §2
**Status:** draft, 2026-08-13
**Owners:** Adam Kerpelman, T. Brian Jones

---

> **Not a spec of record yet.** This draft was walked by three adversarial passes that returned
> **110 findings, 22 of them blocking**. The findings are in `docs/slack-protocol-audit.json` and the
> load-bearing ones are summarised in §12. Read that before building anything here. One finding —
> that the stitcher's music timing is poisoned by `ffprobe format.duration` — was checked against the
> real tool and does **not** reproduce on current inputs; see §12. Treat the rest as unverified.



## 0. What it is

`#convo-farm`, one thread per convo, from the moment files land to the moment a page and an episode are live. Five gates, all emoji, all async: the skill never blocks on a human and a human never waits on a model. Git is the truth and Slack is the interface — every decision either of you makes lands as a commit, and if Slack and git ever disagree, git wins and the skill posts a correction.

Neither of you is the one who runs it. Decisions arrive hours apart, out of order, from phones, and either of you may abandon a review halfway. Everything below is built backwards from that.

---

## 1. The drop

### 1.1 The contract is a directory, and the transport is invisible

A drop is a directory. Not a file, not a Slack upload, not a link.

```
<inbox>/<farm>-<number>/
  drop.json          the manifest — written LAST, always
  master/            the released or mastered episode (0 or 1 audio file)
  tracks/            per-speaker isolated audio, named by person id: adam.mp3, tbj.mp3
  transcripts/       vendor transcripts as delivered (riverside.txt/.srt, scribe-raw.json)
  session/           optional edit source (.sesx, EDL, or a hand-written edit-map.json)
  notes.md           optional free text from whoever dropped it
```

Required: `drop.json`, plus at least one of `master/` or `tracks/`. Everything else optional.

```json
{
  "schema": "drop/1",
  "drop_id": "3f9a1c2e0b74",
  "farm": "zengineering", "number": 98,
  "title": "On Open Source Collaboration", "recorded": "2020-08-22",
  "transport": "sync|web|cli",
  "sealed_by": "adam", "sealed_at": "2026-08-13T21:04:11Z", "sealer": "farm-drop 1.0.3",
  "participants": [
    { "person": "adam", "role": "host", "track": "tracks/adam.mp3" },
    { "person": "tbj",  "role": "host", "track": "tracks/tbj.mp3" },
    { "person": "jane-doe", "role": "guest", "track": "tracks/jane-doe.mp3",
      "contact": "jane@example.com", "invited_by": "adam",
      "briefed_before_recording": true }
  ],
  "timelines": {
    "relation": "identical|edited|unknown",
    "published": "master/098.mp3",
    "session": "tracks/",
    "map": "session/098.sesx"
  },
  "master_has_music": true,
  "files": [
    { "path": "master/098.mp3", "bytes": 58982400,
      "remote_hash": "…", "sha256": "…", "kind": "master",
      "media": { "seconds": 3683.239, "channels": 2, "sample_rate": 44100 } }
  ],
  "manifest_source": "declared|inferred",
  "drop_complete": true
}
```

Three fields exist only because E098 taught us they had to.

**`timelines.relation` is required and has no default.** 098's published master is an *edit* of the session: 8 clips, 6 internal cuts, 87.1 s of conversation removed, and a cold open lifted from 20:41 and **moved** to the front. Master and session diverge by up to 83.44 s and no single offset relates them. A pipeline that assumes master == session ships a transcript of a recording nobody released.

| `relation` | What the pipeline does |
|---|---|
| `identical` | A **claim**, not a default. Stage 2 verifies it by cross-correlating **content offsets, never file durations** — 098's famous 78 ms was three MP3 frames of tail padding on two perfectly aligned tracks. Verification failure downgrades the drop to `edited` and demands a map. |
| `edited` + map | Stage 2 parses the map, verifies it, writes `source.json → edit_map`, posts the timeline audit. |
| `edited`, no map | Stage 2b recovers one by envelope cross-correlation. If no map recovers, **no published timestamp is emitted** and G0 reopens with three named choices. It never guesses an offset. |
| `unknown` | Legal on ingest. Must resolve before stage 3. |

Every published timestamp is on the **master** timeline (`convo-v1-spec.md` §9).

**`master_has_music`** drives stitcher mode selection, and it is not academic. See §8.

**`briefed_before_recording`** is a required boolean on every guest. `convo-v1-spec.md` §10 open question 4 is unresolved; this turns it into a recorded field instead of an answer. You cannot ship a convo without recording which way it went.

### 1.2 Transport-agnostic, by construction

There is exactly one field that differs by transport, and it is `transport`. Nothing downstream reads it except provenance.

| Transport | Who writes `drop.json` |
|---|---|
| **Synced folder** | You run `farm drop <folder>` on the machine that has the files. It normalises names, probes media, computes `sha256` **and** the transport's own content hash, writes `drop.json` last. |
| **Web upload** (D2, not built) | The upload endpoint *is* the sealer. It calls the same `seal()` server-side when the last part completes and writes a byte-identical manifest with `transport: "web"`. |
| **Own recorder** (later) | Same shape, same file. |

A one-shot command at drop time is not the rejected local watcher. The rejected thing was a daemon on a laptop that isn't reliably on. You are already at the machine when you drop files.

**The runner never writes into a drop.** It reads and leaves it alone — the same rule `source.json` already states for the 098 archive. Consumption is a git ref, not a moved file, because moving files inside a syncing folder is how you lose them.

### 1.3 Trigger: cron pull, `*/10 * * * *`

No local watcher — neither laptop is reliably on. No webhook either: the runner takes **no inbound connections** (`research-pass.md` §7), and that sentence is worth more than ten minutes of latency on an event whose human latency is measured in hours.

The inbox is an addressable read-only namespace, not a filesystem. One adapter interface:

```
list(prefix) -> [(path, bytes, remote_hash, rev)]      get(path) -> bytes
```

Two implementations: `dropbox` (App-folder-scoped read-only token) and `blob` (the web-upload target). Both satisfy `research-pass.md` §7 — outbound only, Slack token and model keys, no deploy key.

**The poll never downloads media.** It lists metadata and compares against the manifest. Full `sha256` is recomputed once, after download, at stage 1; a mismatch there fails the stage loudly. That is why the manifest carries two hashes and not one — `remote_hash` decides completeness for free, `sha256` proves the bytes survived the trip.

### 1.4 Completeness — the 60 MB track that is still syncing

**Path A — manifested.** All of:

1. `drop.json` present, parses, `schema: "drop/1"`, `drop_complete: true`
2. Every `files[]` entry present at exactly `bytes` **and** exactly `remote_hash`
3. No file under the drop root missing from `files[]` — an extra file means still-arriving or tampered
4. No partial-transfer siblings anywhere: `*.tmp` `*.part` `*.download` `*.crdownload` `*.icloud` `~$*` `.dropbox.cache` `*(conflicted copy*)`
5. `now − sealed_at ≥ 120 s`

That is COMPLETE on the first verifying poll. No quiescence window is needed, because the hash already proves every byte arrived.

**The manifest is necessary and not sufficient, and this is the whole trick.** `farm drop` writes `drop.json` last *on disk*, but a sync client uploads in whatever order it likes, so a 1 KB manifest routinely reaches the cloud before a 60 MB track. Manifest-present is not a completeness test. Condition 2 is.

**Size alone is not a completeness test either.** An iCloud dataless placeholder reports the full size and a final-looking mtime while containing nothing. Sync clients preserve source mtimes, so a half-transferred file can carry a finished-looking timestamp. Only the content hash sees through both.

**Path B — unmanifested.** Someone dragged files in. Require three consecutive polls spanning ≥20 minutes with an identical file set, sizes and mtimes, no sentinels, and at least one audio file. Then the runner synthesises a manifest, marks `manifest_source: "inferred"`, says so in the thread **and** in the published provenance, opens the branch, and **does not start stage 2** until an operator confirms the file list. Stage 7 refuses to cut clips until someone answers `timelines.relation`.

The obvious bug produces a question in the channel. It never produces a corrupt transcript.

### 1.5 Idempotency — git is the ledger, there is no database

```
drop_id = sha256(sorted (relpath, bytes, sha256) triples)[:12]
```

Content-addressed. Same bytes twice — re-sync, folder rename, re-upload, Dropbox rewrite — is the same drop.

Order is strict and it matters:

1. Clone. Is `drop_id` already claimed in `convos/_drops/index.json`? If yes, **exit silently.** A "still nothing new" post every ten minutes is how a channel gets muted, and a muted channel is a dead review gate.
2. If no: **commit the claim and push it, before posting anything to Slack.** Ref creation on the remote is atomic, so two cron runners firing on the same minute race on git, not on Slack. The loser's push is rejected non-fast-forward and it exits having posted nothing.
3. Then, and only then, open the thread. The claim commit is force-updated with `thread_ts` once the post succeeds. A claim older than 30 minutes with `thread_ts: null` is dead and the next poll takes it over.

Slack posting is separately idempotented:

```
client_msg_key = sha256(convo_id + stage + item_id + content_hash)
```

recorded in `convos/<id>/gates.json`. If the key exists, skip the post. Any stage re-run from any state is safe against double-posting.

A re-drop with **changed** content is a different `drop_id`. It posts a supersede proposal into the **existing** thread. It never opens a second thread and never silently reprocesses.

**Liveness.** If the poller finds nothing for seven days it posts one line. Silence past eight days means the cron died, and otherwise a dead cron is indistinguishable from a quiet month.

---

## 2. Roles

`people/<id>.json` **is** the auth record. The role and the consent model are the same object seen twice, so they live in the same file.

```json
{ "schema": "person/1", "id": "jane-doe",
  "access": { "role": "admin|operator|guest", "slack": "U02ABC…"|null,
              "contact": "jane@example.com", "since": "2026-08-13", "granted_by": "adam" },
  "character": { "consent": { "generative": false, "updated": "2026-08-13" } } }
```

`tech-stack.md` §2 already says guests are opt-in, default to no likeness, and `consent.generative: false` is honoured with no override flag. `convo-v1-spec.md` §3 rule 5 already says guests get checked by the same standard as hosts and get a right of reply before publication. Those are not editorial politeness. They are exactly the permissions a guest role holds: control of their own likeness, and a write path to their own `host_note`. A guest's account is the set of things the editorial rules already promised them. Nothing new is being invented here.

### 2.1 Identity

- **operator / admin** — Slack OIDC. They already have Slack. Do not build a second password store.
- **admin set** — a list in `farms/<farm>/farm.json`. Changing it is an admin commit. Both of you are admin in v1; the role exists so the first non-owner operator is a person record and not a code change.
- **guest** — a single-use signed token. No account, no password, ever.
- **runner** — a machine principal, strictly weaker than an operator. Slack token and model keys, **no deploy key, no merge right.**

Reactions from any Slack user not in `people/` are ignored, and the skill says so once per person per thread. An ignored ✅ that looks like it worked is worse than no reaction at all — without this, anyone invited to `#convo-farm` can publish a page with a thumbs-up.

### 2.2 What each role can do, at each gate

| | admin | operator | guest | runner |
|---|---|---|---|---|
| **G0** adopt drop | adopt, abort, supersede | adopt, abort | — | detect and propose only |
| **G1** research queue | all reactions | all reactions | — | posts; spends only on ✅ |
| **G2** research results | all reactions | all reactions | — | posts |
| **G3** beats + checks | all reactions | all reactions | via packet, only on items that quote them | posts |
| mint / re-mint guest packet | yes | yes | — | delivers |
| **likeness consent** | may set any person to FALSE. **May never set another person to TRUE.** | own only | **sole authority over own** | honours, no flag |
| right of reply | cannot edit a guest's words; may decline to publish a whole check | same | writes it | transcribes it verbatim |
| objection ruling | rules; may reverse an operator ruling inside 7 days | may rule | raises | routes only |
| **G4** publish | 🔒 (not the PR opener) | opens PR, 🔒 after 24 h, 🛑 any time | — | opens PR, holds no deploy key |
| stage 10 ship to Transistor | yes | yes | — | never |
| `people/` records | create, set role | edit own | edit own | writes on instruction |

The consent row is a **one-directional ratchet**, and that is what `tech-stack.md` §2's "no override flag" means when you write it as a permission. Admin is the highest process authority and has zero authority over consent.

### 2.3 Two powers of different force

- **Absolute** — likeness. The guest decides, nobody adjudicates, there is no admin path around it. Default is off and it stays off unless that guest's own commit flips it.
- **Adjudicated** — a content objection to a specific clip or quote. The guest raises it, an admin rules within 7 days, and on operator silence at day 7 it is **auto-honoured**. A guest cannot delete a check; rule 5 says guests get checked by the *same standard as hosts*. What a guest gets unconditionally is a reply that ships inline, verbatim, unedited.

### 2.4 How the right of reply reaches someone who is not in Slack

The reply is a **packet**, and it has a transport-agnostic seam exactly like the drop does.

**v1, today, zero new infrastructure.** The skill renders `reply-packet.html`: every check that quotes that guest, verbatim `claim_as_said`, `what_we_found`, sources, confidence, plus their beats, their likeness status, and a deadline. An admin sends it by email. The guest replies by email. Either of you pastes it into the thread as `reply:c4 <their words>` and the skill commits it verbatim as `checks[].host_note` with their byline.

**v1.5, when the porch exists.** `packet.conversation.farm/g/<token>` serves the same rendered packet and the guest's reply writes the same two fields. Their consent toggle is on the same page. 21-day expiry, single use per device, re-mintable, revocable.

Both paths write `checks[].host_note` and move `consent.json.reply_state`. The protocol cares about nothing else, so building the web path changes none of this.

**The porch is a fourth plane and it is named, not smuggled.** `convo-v1-spec.md` §7 lists "anything with a login" as a v1 non-goal and `tech-stack.md` §0 says the reader plane is static files with no server. Both survive intact: the packet and the future upload UI live on a **separate origin in the producer plane**, and the published convo page stays static, anonymous and cached. One rule holds the line — **the porch never serves a convo page and a convo page never calls the porch.**

### 2.5 Publish blocking, and the two defaults that differ on purpose

A convo with a guest cannot pass G4 until every packet is **resolved**:

| State | Resolves? |
|---|---|
| Returned | Yes |
| Opened, unanswered, past day 21 | Yes — recorded as `reply: none, opportunity: exercised` |
| **Never opened** | **No. Not ever, on any timer.** |

An unopened link is not evidence that the opportunity was delivered, and rule 5 promises a delivered opportunity. Never-opened escalates to a human at day 18 with four named ways out.

Consent defaults **closed** and never opens without action. The right of reply defaults **offered** and closes on a timer. A silent guest can never block the convo forever, and a silent guest can never acquire a cartoon likeness.

### 2.6 Hard blocks — no role approves past these

A 🔒 on a convo with an open hard block is acknowledged, committed, and queued. It is not executed.

1. Any tendril URL not 200 at build time (`convo-v1-spec.md` §6, `CLAUDE.md` #3)
2. Fewer than 2 tendrils on any beat (`convo-v1-spec.md` §6)
3. A likeness present for a person whose `consent.generative` is false (`tech-stack.md` §2)
4. A guest packet not resolved per §2.5
5. `convo.json` invalid against `schemas/convo.schema.json`
6. Page over budget: 2 MB total, 40 KB gz HTML (`tech-stack.md` §1)

These are build-breaking. There is no override reaction and the skill will not offer you one.

---

## 3. The thread

Every message the skill posts, in order, with its actual text.

**The governing rule:** if a message does not change what one of you does in the next five minutes, it is not a message. It is a commit, or an edit to a message that already exists. New messages notify; edits do not. So new messages are for *act now* and edits are for state.

**The length rule:** every message except the research queue is capped at roughly 12 visual lines / 1,200 characters, split at a block seam, never per item. Past that Slack hides it behind a "See more" tap on a phone, and a gate you have to tap twice to read is a gate that dies. The research queue is exempt because `research-pass.md` §2 mandates one numbered message, so it is the one message you will have to expand. Everything else is written so the decision is makeable from the first three lines.

### 3.1 Intake

**M01 — drop verified. This is the thread root.**
Posted to `#convo-farm` as a top-level message. Everything after this is a reply in its thread. The claim ref was already pushed before this posted.

```
🌱 zengineering-098 — On Open Source Collaboration
Drop 3f9a1c2e0b74 verified 09:14 · sealed by adam · via sync · branch convo/zengineering-098

master/098.mp3            61:23   dual mono, music bed baked in
tracks/adam.mp3 tbj.mp3   62:41   mono 44.1k, isolated, 0 ms content drift
transcripts/scribe-raw.json · session/098.sesx · 1 file ignored (not in manifest)

Timeline: edited. Master ≠ session, edit map present, 8 clips / 6 internal cuts /
87.1 s of conversation cut / cold open lifted from 20:41. Every published timestamp
will be on the master timeline. I verify the map at stage 2 before any timestamp ships.
Participants: adam, tbj — no guests, no guest gate on this convo.
Page URL reserved: conversation.farm/zengineering/098

Working: stage 2 transcribe (runner) since 09:14
Nothing for you yet. Next ping: the research queue, ~20 min. ✂️ within 15 min aborts.
```

Reactions: ✂️ abort, 15-minute window only. Nothing else is read.
Lands as: `convos/_drops/3f9a1c2e0b74.json` + `convos/zengineering-098/source.json`, commit `drop: adopt 3f9a1c2e0b74`. Already pushed; ✂️ produces a revert.
Replies: not read.

**This message is edited, never re-posted, as stages complete.** The `Working:` line is the claim display. Transcription finished, 451 turns, 293 zero-duration words, per-stage cost, clips cut — all of it lands here as an edit and in the commit log, and none of it fires a notification. The last line is load-bearing: it tells you to put the phone down, which is the cheapest minute this protocol can give either of you back.

**M01g — guest block.** Replaces the Participants line when a participant has `role: guest`.

```
Participants
• adam — host, operator     • tbj — host, operator
• Jane Doe — guest. Contact on file: j••••@example.com, invited by adam.
  Likeness: not granted (default). Briefed about the checks block before recording: yes.
  Right of reply: not yet sent.
  This convo cannot pass the publish gate until Jane's packet resolves.
/farm guest jane-doe send mints it now. Otherwise it goes automatically when the
checks lock at G3, which is the earliest point the packet is honest.
```

**M02 — drop mid-sync.** Posted once per state, then silent.

```
⏳ zengineering-101 — drop is mid-sync. Not harvesting, nothing spent.

drop.json lists 5 files. Right now:
  ok       master/101.mp3        418.2 MB   hash ok
  ok       tracks/adam.mp3       312.7 MB   hash ok
  PARTIAL  tracks/tbj.mp3         41.2 MB   manifest says 309.4 MB
  MISSING  transcripts/riverside.json
  ok       session/101.sesx        1.1 MB   hash ok

Sealed 8 min ago, so this is exactly what I'd expect. The manifest is 1 KB and reaches
the cloud before a 300 MB track does — that's why I check every file's hash and not just
whether the manifest showed up. Re-checking every 10 min. You don't have to do anything.
```

Reactions: none. Lands as: nothing. Replies: not read.
One more message at the 6-hour mark if it is still stuck, then quiet. Under 6 h an incomplete drop is silent, because a drop that is 40% uploaded is not news.

**M03 — provisional drop, no manifest.**

```
⏳ Provisional drop · zengineering-101 · no drop.json, manifest inferred
The folder stopped changing 32 min ago across 3 polls, no partial-sync markers.
Branch opened. Transcription has NOT started.

9 files, 1.2 GB. Largest: master/101.wav 812 MB.
What I'd expect and don't see: tracks/ has one file for a two-person convo.
No timelines.relation — I'll treat it as unknown and refuse to emit timestamps.
Provenance on the published page will say manifest: synthesized.

Cheap fix: run farm drop <inbox>/zengineering-101 on the machine that dropped it.
✅ the list is right, harvest it · ✍️ + reply names what's still coming · ✂️ not a drop
```

Reactions: ✅ adopt as-is · ✍️ hold and wait for named files · ✂️ discard.
Lands as: on ✅, `manifest_source: "inferred"` and `adopted_by`, commit `drop: adopt <id> (inferred manifest, confirmed by tbj)`. The inferred flag stays in provenance forever.
Replies: ✍️ + reply, one file per line.

Without this message a human drops a folder and hears nothing forever, which is the worst failure this protocol can have.

**M04 — re-drop / supersede.**

```
♻️ New drop for a convo that already has a thread · zengineering-098
8b02f5d19ac3 landed 07:12, sealed by adam. Not the drop this thread ran on.
Changed:   tracks/adam.mp3 (new sha, +12 s) · transcripts/riverside.txt removed
Unchanged: master, tbj track, session

I've done nothing with it. Superseding re-runs stages 2–5 and invalidates the G3
decisions on beats whose timestamps move. 4 of 7 beats survive untouched: b1 b2 b4 b7.

✅ supersede · ✂️ ignore it, keep the harvest as it stands · 🛑 hold
```

Lands as: on ✅, new drop record, surviving G3 decisions replayed from `gates.json`, commit names how many were preserved. Retired decisions go to `reviews.superseded.json` — never deleted.

**M05 — the claim.** One message per convo, **edited in place** as stages change hands.

```
🚧 stage 4b research · claimed by adam · 09:41 · expires 10:11 · runner cf-run-7c2
ref refs/claims/zengineering-098/4b — heartbeat every 10 min
A second run on this convo refuses rather than races. Reviewing is unaffected —
react on anything above at any time.
```

`tech-stack.md` §3 asks for a claim message before every stage. Honoured in intent, changed in mechanism: ten stages is ten notifications against a fifteen-minute budget, and a Slack message has no compare-and-swap so it can race with itself. The lock is the git ref. This message is its shadow, and it is edited, not re-posted.

### 3.2 Gate 1 — the research queue

**M06.** After stage 4a. One numbered message (`research-pass.md` §2). The money gate: nothing paid has run yet.

```
🧾 G1 — approve the research queue · zengineering-098 · 9 questions
React on THIS message; put numbers in your reply. A reply with no reaction is not read.

1  verify     b1 09:15  "Tesla has open sourced all of their patents." True as stated?
2  verify     b3 34:52  Git written by Linus Torvalds, who also created Linux.
3  since      b2 21:26  Apple's closed App Store vs Android openness — what changed since 2020?
4  since      b5 45:33  "Almost everything has an open source counterpart." Still true in 2026?
5  contradict b4 38:12  Strongest good-faith objection to append-only history everywhere?
6  enrich     b3 34:52  Best account of WHY git was written, past the Torvalds trivia.
7  since      b6 52:41  The blockchain-adjacent aside — what happened to that thesis?
8  identify   b2 20:41  The licences they gesture at without naming.
   ⚠️ 4a wrote this as 00:00. The cold open was lifted from 20:41 and MOVED, so 00:00
   addresses audio twenty minutes in. Rewritten against source.json → structure.
9  verify     b7 27:03  Heartbleed was in OpenSSL, undetected for two years.
   Only Scribe has this passage; v0 and Riverside both drop it.

4 of 9 are `since`, which is the right shape for a six-year-old convo. Every `since`
answer must cite a source published after 2020-08-22 or I drop it myself.
All 9: ~$6.10, ~11 min, run in parallel. Convo cap $12, spent $0.41.

✅ run it as written · 🔎 run it and spend harder everywhere · 🛑 hold
Per item, in a reply:   cut: 3      edit: 5 <text>      add: <question>
                        harder: 4   first: 1,6,9
Nothing runs and nothing costs until a ✅ lands here. No timeout starts it for you.
```

Reactions: ✅ approve and authorise the spend · 🔎 spend harder · 🛑 hold · ✂️ abandon the research pass.
Lands as: `research/queue.json`, each item's `human: {decision, by, note}` block (`research-pass.md` §4), commit `G1: queue 8/9 approved, 1 added (tbj)` with trailer `Decided-by: tbj (slack:U02…)`. The ✅ is the spend authorisation and its permalink is in the commit trailer, so the receipt for every dollar points at a human.
Replies: directive tokens at line start, addressed by item number. This is the one place where free text does structural work, because reactions are message-scoped and this message holds nine objects.

Adding a question is the highest-leverage sixty seconds in the pipeline. It is `add:` and not a reaction, because a question is text.

### 3.3 Gate 2 — research results

**M07.** One message per result, as each 4b job returns, async and out of order.

```
🔬 r04 · since · beat b5 · verdict outdated · confidence medium · 4 sources · $0.81
Claim: "Almost everything has an open source counterpart."  — tbj, 2020-08-22

Half vindicated, half inverted, which is more interesting than either. Several major
projects relicensed off OSI-approved terms after 2020; separately, open-WEIGHT models
arrived and changed what "counterpart" even denotes. True about tools, contested about
infrastructure.

Sources — all fetched, all 200 at 15:31, 4 distinct domains
  1 <title> — <publisher> — <pub-date>
  2 <title> — <publisher> — <pub-date>
  3 <title> — <publisher> — <pub-date>
  4 <title> — <publisher> — <pub-date>
✅ `since` rule satisfied: 4 of 4 published after 2020-08-22.
Two share a domain — anti-slop rule 5 keeps one. I picked #2.

Default destination: one tendril on b5 + one check, verdict outdated.
✅ take it · 🧪 checks block only · ✂️ drop · 🔁 rerun (note required) · 🔎 dig deeper
```

**M08 — a thin one**, so the ✂️-without-discussion case has a shape.

```
🔬 r06 · enrich · beat b3 · confidence low · 1 source · $0.31
Q: Best account of why Git was written, past the Torvalds trivia.

One usable link: the 2007 Google Tech Talk. Everything else came back as a restatement
of the Wikipedia article, which research-pass §3 rule 2 says is a show note, not a
tendril. Doesn't clear rule 4 either — nothing here is non-obvious.

Recommendation: ✂️. b3 already has 2 tendrils and one of them is non-obvious.
✅ take it anyway · ✂️ drop · 🔁 narrower question · 🔎 dig deeper (+$0.70)
```

Reactions: ✅ accept in default destination · 🧪 promote to check · ✂️ drop · 🔁 rerun · 🔎 dig · 🔝 keep this one if the budget trims.
Lands as: `research/results/r04.json → human`, commit `G2: r04 → check outdated (adam)`.
Replies: 🔁 requires a threaded reply from the reactor. Absent one within 60 min the skill posts one line asking for it and leaves the item undecided. It never guesses what you meant, and it never re-spends without a note.

URLs are placeholders in this document on purpose. `convo-v1-spec.md` §8 forbids a spec that fakes them, and a spec that fakes them teaches the agent to fake them.

### 3.4 Gate 3 — beats and checks

**M09.** After stage 5 assembles and validates. One message per beat (`tech-stack.md` §3), 5–9 of them, posted 1.2 s apart.

```
🎙 b3 · 13:34–15:52 · tbj · speaker confirmed, 14.2 dB margin · beat 3 of 7
> "Git is basically the only tool where the append-only history is the point, and
> everybody else is still overwriting rows in a database."

Context: follows the Torvalds detour, sets up Adam's argument two beats later.
Clip clips/b3.mp3 · 18.4 s · mono Opus · 61 KB
  Bounds from decoded frames, never ffprobe format.duration. Snapped to words with
  duration > 0, padded 250 ms, 1.1 s clear of the edit boundary at 1253.292.
Tendrils 3 — all ✅ at G2, context only     Checks 1 — c2 off, medium

You are deciding the beat, not the research. Leave the tendrils alone unless the beat
changes what they should be.
✅ ship it · ✂️ cut · 🔁 rewrite the claim (reply `claim:`) · 🔎 tendrils are thin
⚠️ c2 is unfair, pull it (reply says why) · 🧪 there's an unchecked claim of fact here
```

Reactions: ✅ · ✂️ · 🔁 (note required) · 🔎 · ⚠️ (note required) · 🧪.
Lands as: `convo.json` beats/checks + `gates.json`, commit `G3: b3 approved (adam)`, trailer `Decided-by:`.
Replies: read only from the person who reacted, after their reaction, before the gate closes. `claim:` at line start replaces the sentence verbatim. `note:` attaches without changing anything.

**One reaction from either of you decides an item.** No quorum. Requiring both across 7 beats and 9 results is how a review gate dies when both reviewers have small children.

**M10 — split decision.** The only disagreement that earns an interruption.

```
👀 Split on b4: adam ✅ 22:31, tbj ✂️ 07:14 next morning.
✂️ beats ✅ — cautious wins, and the objector is asleep and can't argue. b4 is cut.
Both marks are in gates.json, so the disagreement survives in the diff even though
only one outcome does. tbj placed it, so tbj or an admin clears it.
Everything else moved on without it — 5 of 6 beats are through and stage 7 is running.
```

Applied by the precedence lattice in §6, which is order-independent: this resolves the same whether Brian's ✂️ arrived first or ninth. The machine resolves it, and then it tells you, because silently overriding your co-host is the one place where silence is worse than a message.

**M11 — reaction on a superseded version.**

```
👀 adam ✅'d b3 (v1), which no longer exists.
b3 was rewritten at 19:41 after tbj's `claim:` and reposted as b3 (v2), so I did NOT
apply it. Stale approvals can't ship. Current b3: <permalink>
If v1 was what you wanted: reply `revert: b3 v1`.
Every beat message carries its version. No `v2` in the header means it's current.
```

Logged to `gates.json` with verb `superseded`, so the record shows the person did react.

**M12 — un-react after the decision committed.**

```
👀 tbj removed ✂️ from r04. I committed that 14 min ago as b2f0913.
Removing a reaction doesn't undo a commit — git is where decisions live, Slack is where
they get made. Before a stage runs, changing your mind is free and it never happened.
After, it's a revert: 🛑 on the r04 message, or reply `revert: r04`.
```

**M13 — unparsed line.**

```
❓ Couldn't parse 2 lines in your reply to G1. Everything else applied → 8c3f21a.
  "5 — narrow this to the OSI definition"     did you mean `edit: 5 …`?
  "also can we check the FSF thing"           did you mean `add: …`?
Nothing was silently dropped. Re-post those two and I'll take them.
```

A human never silently loses an instruction. Everything else in the thread stays unparsed and unmentioned, because a parser that reads all thread text will eventually act on a joke, and both of you are funny.

### 3.5 The guest gate

**M14 — packet sent.** Automatically when G3 locks the checks, or on `/farm guest <id> send`.

```
🙋 Guest packet sent — Jane Doe · zengineering-104
Emailed j••••@example.com 11:02 by adam. Expires 2026-09-03, 21 days. Reminders day 3, 7, 14.
Briefed about the checks block before recording: yes.

She sees: her 4 beats, her 2 clips, the 3 checks that quote her, and the likeness ask.
She does not see: this thread, the other beats, the queue, or your reactions.
She can do four things: grant or withhold likeness · reply per check · object to a clip
· mark read.

Publish is blocked until this resolves. State: sent, unopened.
When she replies by email, either of you paste it here as `reply:c4 <her words>` and I
commit it verbatim with her byline.
🔁 re-mint to a different address (address in reply) · ✂️ revoke (admin)
```

**M15 — packet returned.**

```
🙋 Jane Doe returned her packet · 14:31, 2 days after send

Likeness — WITHHELD. consent.generative: false, committed a4f19c2. Typographic card.
  This is absolute. There is no override flag and no admin path around it.
Right of reply — used on 1 of 3 checks.
  c4 off — "I said 'roughly a third' and I'd stand by it, but I was talking about seats,
  not revenue. The check is comparing me to a revenue number."
  → ships inline as checks.c4.host_note, byline Jane Doe. Nobody edits her words.
  c2, c5 — read, no reply. Recorded reply: none, opportunity: exercised.
Objection — 1 raised, needs a ruling.
  b6 clip 41:12–41:38 — "this is me repeating a client's name, please cut it."
  ⚠️ honour the cut · ✅ decline (reply with the reason — it goes to her verbatim) · 🛑 talk first
  Rule within 7 days. Her packet promised her that. On silence at day 7 I cut it.

Publish still blocked on b6. Everything else on her side is resolved.
```

**M16 — never opened, day 18.** The case that must not auto-resolve.

```
🙋 Jane Doe — packet expiring · sent 18 days ago, NEVER OPENED
Reminders day 3, 7, 14. No open event on the link.

Right of reply requires a delivered opportunity, and an unopened link is not evidence of
one (convo-v1-spec §3 rule 5). So this does not time out into a publish. Ever.

✅ I reached her another way and she's seen it — reply with HOW, it goes in provenance
🔁 mint a new packet to a different address — reply with the address
✂️ pull her beats and the checks that quote her, publish without them
🛑 hold the convo

Opened-but-unanswered auto-resolves at day 21. Never-opened does not, and will not.
```

✅ with no evidence line is ignored. That is the one place this protocol deliberately refuses to be convenient.

### 3.6 Gate 4 — publish

**M17.** Stage 8 has rendered the page, materialised the wrap folder, run the stitcher, and opened the PR. Two artifacts, one decision.

```
🚜 G4 — publish · zengineering-098 · PR #41 opened by adam 16:02
Preview → https://pr-41.preview.conversation.farm/zengineering/098

THE PAGE
7 beats · 19 tendrils, 19/19 200 at build, 12 domains · 5 checks (2 confirmed, 1 off,
1 contested, 1 outdated) · 3 seeds · full transcript in Dirt
31.4 KB gz HTML · 12.1 KB inline CSS · 0 KB JS · 1.71 MB of the 2 MB budget
LCP 0.9 s Slow-4G · CLS 0.004 · reads with JS off
Provenance complete: 3 ASR passes, attribution confirmed off per-track audio, the
speaker caveat published verbatim, $6.14 spend recorded.

THE EPISODE  _wrap/zengineering-098/ · stitcher --bare · 62:14
Master already carries the 2020 music bed, so no template wrap and no double music.
Outro bump 11.2 s: "Show notes, sources and the full transcript are at conversation
dot farm slash zengineering slash zero nine eight."
Main Convo bytes are sha-identical to the reviewed master.

Hard blocks: none. Gates: G1 ✅ tbj · G2 ✅ both · G3 ✅ 7/7 · guests: none
adam ran this, so tbj ships it. If tbj hasn't in 24 h, adam's own 🔒 is enough.
🔒 publish · 🛑 hold · ⚠️ + reply names something wrong on the page
✅ does nothing here.
```

Reactions: 🔒 publish · 🛑 hold · ⚠️ defect (must be named).
Lands as: 🔒 writes the approval into `gates.json` and onto the PR. **CI merges. The runner cannot** — it holds no deploy key and no merge right (`research-pass.md` §7, `CLAUDE.md` #6). The merge commit is the decision.
Replies: ⚠️ requires a reply naming the defect; it reopens G3 on that item only, not the whole gate.

**✅ is not accepted at this gate.** The one irreversible-ish action must not share a glyph with the one you tap all day. Reaction fatigue must not be able to ship a page.

**M18 — live.**

```
🌻 zengineering-098 is live — https://conversation.farm/zengineering/098
Merged by CI on tbj's 🔒 at 21:47. Deploy 1m 52s. All 19 tendrils re-fetched in CI, 19/19 200.
convo.json state: published · e91b7a4 · tagged zengineering-098-v1

Left, human, whenever: upload _output/098-final.mp3 to Transistor.
/farm wrap 098 prints the description with the URL already in it.

$6.14 model · 41 min wall clock · 12 minutes of the two of you (adam 7, tbj 5).
The old show notes for this episode were four links. This page has 19, every one fetched.
```

Reactions: none. Lands as: already landed. This message is the receipt.

The human-minutes line is not decoration. It is the only feedback loop on the number this protocol exists to protect.

### 3.7 The wrap

**M19 — episode rendered.**

```
🎧 Episode rendered · zengineering-098 · stitcher --bare · 62:14 · 71.4 MB
_output/098-on-open-source-collaboration-final.mp4 · loudnorm −16 LUFS · sha 3c9b…
Intro: none — master carries the 2020 bed. Outro bump 11.2 s appended, names the URL.
URL checked 200 two minutes ago.
episode.json committed: mode, every segment path + sha256, music identity, stitcher
commit, intro asset version, the exact URL string spoken.
Re-running with this episode.json produces this file byte for byte.

Render it where the media lives:
uv run python stitch.py "../Podcast Episodes/098 - On Open Source/" --bare
```

**M20 — the RSS packet.**

```
📦 RSS packet · convos/zengineering-098/rss.json @ e77c210
The conversation is the core. This is the seam where material gets added around it on
the way to the feed.

audio       _output/098-final.mp4  sha d41f8a…
canonical   conversation.farm/zengineering/098 — verified 200 at 14:02
identity    title / number / recorded / participants, from convo.json. Typed once.
unmodified  Main Convo bytes == reviewed master bytes. shas equal.
additions[] empty

Nothing reaches the feed that isn't named in additions[]. That's the guarantee.
What goes in additions[] is undecided and I'm not deciding it. See §8.

Standing rule: anything typed straight into Transistor is invisible to this pipeline
and will be silently wrong the next time the page rebuilds. Argue with rss.json.
```

### 3.8 When something goes wrong

**M21 — dead tendril at build.** Build-breaking (`convo-v1-spec.md` §6, `CLAUDE.md` #3).

```
⛔ Build failed · zengineering-098 · one dead tendril. Nothing published, nothing lost.
t11 <url> — 200 at research on 2026-08-14, 404 now, checked 3× at 60 s apart.
b5 keeps 2 tendrils without it, so the beat still clears the floor.
Wayback has a 2026-08-14 snapshot, 200: <archive-url>

A dead link failing the build is the check working. On a page whose premise is
self-fact-checking, a 404 in the sources is the worst bug we could ship. No override.
✂️ drop it · 🔁 re-research, ~$0.60 · reply `swap: t11 <url>` · reply `archive: t11`
```

**M22 — crash after spending money.**

```
⛔ stage 4b crashed · zengineering-098 · $4.10 already spent · 6 of 8 done
Died on r07, ReadTimeout after 3 retries. The 6 finished results are committed at
b2f0913 and posted above — react on them whenever, they're real. Claim released.
The receipt commits before the result is parsed, so a crash after spend is visible.

reply `retry: r07,r08` — rerun only those two, ~$1.60
reply `accept-partial` — assemble from the 6 and move on
✂️ — abandon 4b, keep the 6, spend nothing more
I will not retry on my own. Paid work never retries without a human, and a bare
`retry:` with no list is refused — that's how you pay twice.
```

**M23 — cost cap.**

```
⛔ Cost cap hit · zengineering-098 · $12.04 of $12.00. Hard stop mid-queue.
Done: 7 of 9. Not run: r08, r09.  transcribe $0.41 · extract $0.18 · research $11.45
reply `cap: 18` (admin) to raise it for this convo only · `accept-partial` to assemble with 7
The cap is per convo and resets nowhere. It's there so a runaway job costs a coffee.
```

**M24 — branch conflict.**

```
⛔ convo/zengineering-098 won't fast-forward. Someone pushed while I was working.
mine   e01ab22  stage 5 assemble, runner on behalf of tbj, 21:02
theirs 77c3d40  stage 4b research, adam, 20:52
I did NOT rebase and did NOT force. My work is parked at
refs/parked/zengineering-098/stage5-e01ab22 — safe and reachable.
reply `take-mine` · `take-theirs` · `rebase`. I'll post the resulting diff before pushing.
This means a claim expired mid-run. Worth a look at the runner log if it happens twice.
```

**M25 — Slack rate limit or outage.**

```
⛔ Slack rate-limited me at 20:14. 6 beat messages queued, posting 1 per 1.2 s.
Nothing is lost — the stage committed at 2f19b04 before the first post went out. If they
arrive out of order, the beat id in each header is the truth, not post order.
(Full outage: every message I would have sent commits to convos/<id>/undelivered.jsonl
and flushes on the next poll. An outage delays the conversation. It never loses a decision.)
```

### 3.9 Housekeeping

**M26 — nudge**, at +24 h and again at +72 h, listing only what is undecided.

```
⏳ G3 still open · zengineering-098 · 4 of 7 decided, 22 h in
Decided: b1 ✅ adam · b2 ✂️ tbj · b3 ✅ adam · b5 🔁 tbj (rewrite queued)
Waiting on: b4, b6, b7. Three messages above, one reaction each. ~90 seconds.
Next nudge in 48 h, then I stop asking.
```

**M27 — stalled**, once, at 7 days, then silence forever.

```
😴 zengineering-104 is stalled · G3 open 7 days, 3 beats undecided.
I'll stop nudging. `/farm status 104` when you come back, or ✅ this to resume nudges.
Branch, decisions and costs are all safe. Nothing expires except Jane's packet, 4 days left.
```

**M28 — poller liveness**, once every 7 idle days.

```
📡 Poller alive, no drops in 7 days. Last successful poll 14:20 UTC.
```

Silence past eight days means the cron died.

@-mentions only past 24 h of no movement, and only between 08:00 and 21:00 in that person's timezone. The skill posts whenever it likes and pings almost never.

---

## 4. The reaction vocabulary

**Kept: `tech-stack.md` §3's set.** It is the canonical table inside the skill's own spec, it is the larger vocabulary, and ✅ / ✂️ / 🔁 already agree across both docs. Keeping it is the smaller edit.

**Renamed: `research-pass.md` §2's ⚠️ "make it a check" → 🧪.** That emoji was the entire collision — it meant "this check is unfair, pull it" in one doc and "promote this to a check" in the other, which is as close to opposite as a vocabulary gets. ⚠️ keeps `tech-stack`'s meaning, because it is the only "this should not be public" mark in the system and it must never be ambiguous.

**Folded, no rename needed:** research-pass's "approve-as-tendril" is ✅ (accept in the default destination); "drop" is ✂️; "rerun" is 🔁. ✍️ and 🔝 carry over untouched, generalised one step each.

**Added: 🧪 and 🛑.** Two new emoji total.

**Sharpened: 🔒.** `tech-stack.md` §3 had it as "locked, ready for publish gate." It is now the publish act itself, valid only on a G4 message.

| Emoji | Verb | Means — everywhere, at every gate | Valid on | Note? |
|---|---|---|---|---|
| ✅ | approve | Take this as written, in its default destination | every gate except G4 | no |
| ✂️ | cut | Remove it. It never ships. | every gate | no |
| 🔁 | redo | Regenerate this one. My reply says what to change. | G1 G2 G3 wrap guest | **yes** |
| 🔎 | dig | Not wrong, thin. Spend more here. Costs money. | G1 G2 G3 | no |
| 🧪 | check | This belongs in the checks block, not as a tendril | G2 G3 | no |
| ⚠️ | pull | Unfair, wrong-headed, or unpublishable as framed. Pull it and log the category. | G3 G4 guest objection | **yes** |
| 🔝 | first | Run first, spend most, survive a budget trim | G1 G2 | no |
| ✍️ | add | My reply is new material — a question, a file list, a URL | G0 G1 | **yes** |
| 🛑 | hold | Stop this **gate**. Nothing proceeds until whoever placed it clears it. | every gate | **yes** |
| 🔒 | ship | Publish. Merge the PR. | **G4 only** | no |

Machine-only, never typed by a human: 👀 (read your marks, applied) and ❓ (couldn't parse that, or you're not an operator).

### 4.1 Three rules that make the table hold

**Scope.** ⚠️ is a verdict on an **item** — pull this one thing, the machine acts. 🛑 is a verdict on a **gate** — stop everything here, and it is the only reaction the skill is allowed to be unable to action. They can never be confused because they never apply to the same object.

**Disjointness.** The ten vocabulary emoji **never appear as decoration in message text.** Message headers draw from a strictly separate set: 🌱 🚧 🧾 🔬 🎙 🙋 🚜 🎧 📦 🌻 ⏳ ⛔ ♻️ 👀 ❓ 💸 📡. If you see ✅ in a message body it is telling you what a reaction would do, never reporting a status. Nobody ever reacts to the wrong thing because the message looked like it already had a reaction on it. This is why the "build failed" header is ⛔ and not 🛑 — 🛑 is vocabulary, and a header that is also a verb breaks the rule it belongs to.

**Message-scope.** A reaction lands on a message, not on a line. Anything addressing one item inside a multi-item message must be a directive token in a reply. That is why G1's nine questions take `cut: 3` and `edit: 5 …`, while ✅ on the message acts on all nine.

### 4.2 Unknown emoji, and skin tones

An unlisted emoji is ignored and tallied. Three uses of the same one gets one message asking to add it to the table or stop. A vocabulary that quietly accretes private meanings has stopped working.

**Normalise skin-tone modifiers before matching.** ✍️ arrives as `writing_hand::skin-tone-3` for anyone with a default tone set — a distinct reaction name in the API. Strip the modifier or those reactions are silently ignored, which is the most annoying possible bug and the hardest to notice.

### 4.3 Edits this requires

- `docs/research-pass.md` §2 — replace ⚠️ with 🧪 in the results-gate line and in the ASCII flow diagram.
- `docs/tech-stack.md` §3 — append 🔝, ✍️, 🧪, 🛑 to the existing table; change 🔒's gloss from "locked, ready for publish gate" to "publish — merge the PR, G4 only".

Nothing else in either document changes.

### 4.4 Where every mark lands

`research-pass.md` §4's `human.decision` enum grows to match, and it is the same file, not a second bookkeeping system:

```
approved | cut | redo | deepen | check | pulled | first | held
```

renamed from `tendril|check|dropped|rerun`. That file is the training set §4 asks for.

---

## 5. Free text

A reaction cannot carry an argument. So this is mechanical, and there are exactly three places.

**1. A threaded reply to the message you reacted to, from the same person.** Bound by `(message_ts, user_id)`, read any time before the stage that consumes it runs. 🔁, ⚠️ and 🛑 without such a reply stall that one item and get a one-line nudge. Everything else in the gate proceeds.

**2. A reply beginning with a directive token at the start of a line.** No reaction needed. One directive per line.

| Token | Where | Does |
|---|---|---|
| `cut: 3` | G1 | drops queue item 3 |
| `edit: 5 <text>` | G1 | rewrites the question |
| `add: <question>` | G1 | appends a queue item |
| `harder: 4` `first: 1,6,9` | G1 G2 | spend / order |
| `claim: <sentence>` | G3 | replaces the beat's claim verbatim |
| `note: <text>` | any gate | attaches text, changes no state, commits as `human.note` |
| `reply:<check-id> <text>` | guest | commits the guest's words verbatim as `host_note` |
| `decline:<check-id>` | guest | records a refusal to comment, which also ships |
| `swap: t11 <url>` `archive: t11` | build failure | replacement tendril, used only if 200 |
| `recut: b3 in=… out=…` | clips | explicit bounds from a human ear |
| `revert: <id>` `revert: b3 v1` | any | undo a committed decision |
| `retry: r07,r08` `accept-partial` `cap: 18` | failures | recovery, explicit lists only |
| `release: <stage>` `take-mine` `take-theirs` `rebase` | concurrency | §6 |
| `add-rss: <kind> <source>` | wrap | §8 |
| `extend: 48h <reason>` | guest | admin/operator only |

`waive:` is parsed and **visibly refused** with one line, because refusing in public beats ignoring in private.

**3. The PR body and PR review comments at G4**, mirrored into the thread so the argument stays in one place.

Everything else in the thread is human conversation. It is never parsed and it is never lost — the whole thread exports to `convos/<id>/thread.jsonl` and commits at publish, so the argument is preserved beside the decision. Every apply summary ends with "read N replies, ignored M," which makes the boundary visible instead of mysterious.

A line that *looks* like a directive and doesn't parse is echoed back once, verbatim, as "not parsed." A human never silently loses an instruction.

---

## 6. Concurrency and claims

Six mechanisms. None of them is a mutex a human has to think about.

**1. Drops — git is the lock.** The claim commit pushes before anything posts to Slack. Two cron runners race on a non-fast-forward push, not on Slack. The loser exits having posted nothing. No double thread, no double spend.

**2. Stages — a claim ref, not a Slack message.** `refs/claims/<farm>-<number>/<stage>`, created with a create-only push. Non-fast-forward pushes to an existing ref are rejected by default, which is a compare-and-swap on the remote with no new infrastructure and no second source of truth. Claims are per `(convo, stage)`, so reviewing beats never blocks a research run. Expiry is 30 minutes (`tech-stack.md` §3), refreshed by a heartbeat every 10 minutes, so a 20-minute research job keeps its lock and a dead run's claim genuinely expires. The Slack claim message is the mirror. Git wins on disagreement and the skill posts a correction.

**3. The runner claims like a human.** Cron gets no special path, as operator `runner` with `on_behalf_of` set to whoever's ✅ authorised the stage. So the claim always names a human and `git log` always answers "who spent this money."

**4. Reacting never needs a claim.** Gates are read-only. Applying decisions is itself a claimed stage called `apply`, so simultaneous reactions are fine and only the write is serialised. Reviewing is always allowed, always, including while a stage is running.

**5. Out-of-order decisions — a precedence lattice, not last-write-wins.**

```
🛑 > ⚠️ > ✂️ > 🔁 > 🔎 > 🧪 > 🔝 > ✅
```

The cautious decision wins, and more work beats less work. Adam ✅ at 09:00 and Brian ✂️ at 22:00 resolves identically to the reverse order. **This must be order-independent by construction**, and here is the blunt reason why: Slack's `conversations.replies` returns reactions as `{name, users[], count}` with no timestamps at all. Reaction times exist only in `reaction_added` events, which need an inbound endpoint or a persistent socket — both denied to a stateless cron runner by `research-pass.md` §7. **Any rule that orders reactions in time is unbuildable here.** Write the merge so it never needs to.

🔒 sits outside the lattice. It is an act, not a verdict on an item: it executes only when every hard block in §2.6 is clear and no 🛑 stands.

**6. Apply is idempotent.** `apply_key` = hash of the `(object, actor, verb)` set read. If HEAD already carries that key, exit 0. A crashed apply is safe to re-run blind.

**Versions.** Every object message carries `v1`/`v2` in its header. Reactions on a superseded version are ignored, logged with verb `superseded`, and the actor is told where to re-react. A stale ✅ can never ship.

**Branches.** One per convo, `convo/<farm>-<number>`, as the durable lock. On a non-fast-forward push the runner **never rebases and never forces** — it parks at `refs/parked/<id>/<stage>-<sha>` and asks. "I lost the race" is always recoverable and never destructive.

**Abandonment.** A half-reviewed gate is a valid state. Decisions are per object and independent, so the skill applies what it has and leaves the gate open only on the rest. **No gate ever requires completeness to make progress on the part that is decided.** That is the whole answer to "either of you may walk away halfway."

**Publish.** 🔒 from an admin who did not open the PR. If 24 h pass with no 🔒 and no 🛑, the opener's own 🔒 becomes sufficient. Two-key by default, no deadlock on a bedtime, and either way **CI merges — the runner writes approval state and nothing else.** That keeps `research-pass.md` §7's one sentence literally true.

> Build note: a merge performed with the default `GITHUB_TOKEN` does not trigger downstream workflow runs. The merge job needs a GitHub App token or a PAT, or the deploy silently never fires and you will spend an afternoon on it.

---

## 7. Failure modes

Designed backwards from these. The happy path is what's left when they're all handled.

| # | Failure | Detected by | Visible as | Recovery |
|---|---|---|---|---|
| 1 | 60 MB track syncing when cron fires | per-file `remote_hash` vs manifest | M02, once per state | automatic, re-checks every 10 min |
| 2 | iCloud placeholder — full size, right mtime, no bytes | `remote_hash` mismatch; size alone passes | M02, PARTIAL row | same as 1. This is why size checks were rejected |
| 3 | Files dropped, no manifest | 3 stable polls ≥20 min | M03 provisional | ✅ or run `farm drop`. Provenance says `synthesized` on the page |
| 4 | Master is an edit, no map | stage 2b recovery fails | G0 reopens with `timeline: master-only / tracks-only / abort` | human picks. **Never guesses an offset** — a single offset is wrong by up to 83.44 s on 098 |
| 5 | `ffprobe format.duration` | never used for a bound anywhere | decoded length printed beside the estimate | n/a. 5.510 s short on 098's master |
| 6 | Same drop harvested twice | content-addressed `drop_id` in the ledger | nothing — skipped silently | n/a |
| 7 | Two runners on one poll | create-only ref push fails | nothing | loser exits 0 |
| 8 | Runner dies mid-stage | heartbeat stops, 30-min expiry | claim message edited to "expired" | next poll resumes; stages are idempotent |
| 9 | Crash after spending money | receipt commits **before** the result parses | M22 with exact dollars | `retry:` with an explicit list, or `accept-partial`. Never auto-retries |
| 10 | Budget runaway | per-convo cap | M23 | `cap: <n>`, admin, committed — nobody raises a cap invisibly |
| 11 | Tendril 200 at research, 404 at build | build-time fetch ×3 | M21, PR not opened | `swap:`, `archive:`, or ✂️. No override offered |
| 12 | Reaction on a superseded version | version in the header | M11 | `revert: b3 v1` |
| 13 | Un-react after the stage ran | reaction-removed vs `gates.json` | M12 | 🛑 or `revert:` |
| 14 | Slack message edited after it was consumed | commit records the hash of the text it acted on | one notice with both versions | `revert:` then re-react |
| 15 | Branch won't fast-forward | push rejected | M24, work parked | `take-mine` / `take-theirs` / `rebase` |
| 16 | CI red after merge | job status on main | one line: page NOT live, readers still see the previous build | `retry-ci` / `revert-merge` |
| 17 | Slack 429 | 429 | M25 | automatic backoff; beat ids are the truth, not post order |
| 18 | Slack down entirely | post fails after retries | nothing, until it's back | `undelivered.jsonl` flushes on the next poll |
| 19 | Guest never opens | no open event by day 18 | M16, four named exits | **never times out into a publish** |
| 20 | Guest objection unruled | 7 days | one line | auto-honoured, clip cut. The packet promised her that |
| 21 | Consent withdrawn after images generated | consent re-read at **build** time, not generation time | G4 preflight: "4 renders deleted, typographic card substituted" | automatic, no override anywhere |
| 22 | Non-operator reacts | Slack user not in `people/` | ❓, once per person per thread | add them by PR |
| 23 | Unknown emoji | not in the table | ignored, tallied; one message at 3 uses | add it or stop |
| 24 | Skin-tone modifier | `::skin-tone-N` suffix | nothing — normalised before matching | n/a, but get this right or ✍️ silently dies |
| 25 | Both of you react opposite | two incompatible marks on one object | M10, naming which won | lattice resolves, order-independent |
| 26 | Review abandoned | no movement 24 h / 72 h / 7 d | M26, M26, M27, then silence forever | `/farm status` |
| 27 | Nobody ever finishes | same | nothing. **No auto-approve, ever** | deliberate |
| 28 | Cron dies | no poll for 7 days | M28 stops appearing | silence past 8 days is the signal |

Two of these deserve saying out loud.

**A failing hash is not an error.** It is a file still syncing. Stay silent and retry. A cron that cries wolf every ten minutes gets muted, and a muted channel is a dead protocol.

**Nothing auto-approves.** A convo can sit half-reviewed forever and this protocol will let it, at zero cost. A timeout that publishes unreviewed work is a lie about the review having happened, on a page whose entire premise is publishing where we were wrong.

---

## 8. The stitcher, the outro bump, and the RSS seam

### 8.1 Which gate

**G4 — one 🔒 ships both artifacts.** The reason is structural, not convenient: the outro bump *says* the URL and the page *is* the URL. If they were two decisions they could disagree. Making them one decision makes disagreement impossible. So stage 8 becomes render + stitch + commit, G4's message shows two artifacts, and stage 10 stays a human uploading an approved file. The human gate count is unchanged.

A gate on a promised artifact is not a gate. The episode is finished before anyone approves it.

### 8.2 Mode selection is data, not a human choice

```
drop.json.master_has_music == true  →  stitcher --bare
otherwise                           →  stitcher --template
```

This is not academic. E098's master already carries the Hendrix rework baked in — `source.json → external_dependency.placements` puts it at master 0.000–32.731 and 3634.018–3683.186. Template-wrapping it lays the new Zengineering tune on top of the old one. So 098 ships `--bare`: a card plus the finished audio, exactly the Ep-102 case bare mode exists for. Episodes 103+ carry no baked music and go `--template`.

### 8.3 The template folder

Exactly the convention the stitcher already documents:

```
_wrap/<farm>-<number>/
  Intro/          intro-v<n>.mp3      the standing recorded intro
  Main Convo/     <the reviewed master, byte-identical>
  Outro/          outro-bump.mp3      auto-generated, names the URL
  Episode Cards/  <16:9>.png <1:1>.png  picked by probed aspect ratio
  Zengineering Intro Tune w-Fade.mp3
  metadata.json   number, title, slug from convo.json
```

**The standing recorded intro** — Adam's "introduces where the conversation came from" — is a per-farm asset at `farms/<farm>/assets/intro-v<n>.mp3`. Re-recording it is an admin commit and bumps the version, because it changes every future episode. `episode.json` pins the version used, so a 2027 re-render of a 2026 episode reproduces the 2026 intro.

**The music timing math is the stitcher's and is not reimplemented.** `music_starts_at = pre_segment_duration + gap/2 − sync_seconds`, defaults `gap 7 s`, `sync 22 s`, from `config.yaml > template`. Negative means start at t=0 with a `file_offset`. The fades are baked into the MP3. G4 prints both computed cue times so a wrong one is visible before it ships, and the protocol never recomputes them.

**The runner assembles and validates. It does not render.** Episode video is GB-scale and the runner is stateless. It runs `--dry-run` to confirm the filter graph builds, then puts the command in the message. The render happens on whichever machine has the media.

### 8.4 The seam is called the wrap

`convo-v1-spec.md` §1's "The podcast ships unchanged" is **retired**, and so is §4 stage 10's "Unchanged from today." The raw conversation is the core, and material is added around it on the way out to RSS.

- `convo.json` + the page = **the conversation.** Frozen at G3.
- `episode.json` (`wrap/1`) + `rss.json` (`rss/1`) = **the wrap.** Everything added around it.

Stage 10 consumes those two files and nothing else from the editorial side. That is the seam.

**What the protocol guarantees, and only this:**

1. **The conversation crossing the seam is byte-identical to what shipped on the page.** `Main Convo/` is the reviewed master, unmodified, sha256 recorded. Additions are strictly *around* it, never inside it. The wrap may not re-edit the conversation, which is what keeps the page's timestamps and the feed's audio referring to the same thing.
2. **The show-notes URL is knowable before the wrap renders.** `conversation.farm/<farm>/<number>` is deterministic from `drop.json` at ingest, so the bump can be built at stage 8 and the page and the audio can ship in either order.
3. **The wrap is versioned and re-renderable.** Same manifest in, same file out. New material later is a new wrap version and a re-render, never a hand edit and never a silent re-master.
4. **Nothing reaches the feed that is not named in `additions[]`.** Every entry carries `{kind, source, rendered, added_by, decided_on}`. If it's in the feed and not in that array, that's a bug.

**What the protocol does not decide, deliberately.** Adam's words: *"the conversation will be at the top, and as it flows into the RSS feed, we should add some stuff on top of it. I don't know exactly about that piece yet."* So `additions[]` is an ordered, open, append-only array with provenance on every entry, and it ships empty until somebody calls it. Candidates that have been said out loud and chosen by nobody: chapter marks from the beats, the tendril list as show notes, the checks rendered as a "here's what we got wrong" paragraph in the description, a written summary, an RSS-only extra segment. None of those is decided and none is implied by this design.

Deferring costs nothing, and that is the point of naming a seam before filling it: whatever gets chosen is a new directory in the wrap folder and a new entry in the manifest. No stage upstream of 8 learns about it, the page never learns about it, and guarantee 1 means it can never reach into the middle.

**One standing rule, because this is where the pipeline leaks.** Anything typed straight into Transistor is invisible to this protocol and will be silently wrong the next time the page rebuilds. Argue with `rss.json`, not with the podcast host. The G4 message says exactly that, every time.

**The concrete consequence to write down:** the page's Dirt block links the *conversation* audio; the RSS feed carries the *wrapped episode*. They are two artifacts of different lengths, and the page says which one it is offering. That sentence replaces "The podcast ships unchanged" in `convo-v1-spec.md` §1.

---

## 9. Human time

Per convo, split across the two of you, spread over days. Neither of you ever sits and waits.

| Gate | Whose | Minutes | What you actually do |
|---|---|---|---|
| G0 drop | either | 0.3 | usually nothing — auto-adopts a declared manifest. Only a provisional drop asks |
| G1 queue | either | 3.0 | read 9 numbered lines, one reaction, maybe two numbers in a reply |
| G2 results | either | 4.0 | ~8 messages at 30 s each; thin ones get ✂️ without discussion |
| G3 beats | either | 4.0 | 5–9 messages, one reaction each, one reaction decides |
| G4 publish | the other one | 1.5 | read two artifact blocks, 🔒 |
| **operator total** | **combined** | **~13** | across a week, in gaps, from phones |
| stage 10 upload | either | 3.0 | human by design; `/farm wrap` prints the description |
| guest packet | *the guest* | 5–7 | not on your budget. Bounded, once, on their own page |

`research-pass.md` §6 caps the two research gates at 10 minutes combined. G1 + G2 is 7 here, inside it. The 13 covers the whole pipeline, which that budget never claimed to.

Be honest with yourselves about felt time: 13 minutes assumes no context reload, and between meetings you will reload every time. Call it 16–18 in practice.

**The failure signal, stated the way `research-pass.md` §6 states it.** If G1 + G2 exceeds 10 minutes, stage 4a's extraction is bad and that is the thing to fix. If G3 exceeds 6 minutes, segmentation is producing beats that need arguing about, and that is stage 3's bug. Never the reviewer's patience.

**What protects the budget:**

1. Reactions do the common cases. Free text only where a reaction genuinely cannot carry the meaning.
2. Every gate message says what happens if you do nothing — always "nothing" — so nobody holds a deadline in their head.
3. Already-approved objects are shown collapsed and need no second reaction. G3 says out loud "you are deciding the beat, not the research," which is what stops G2 and G3 charging twice for the same work.
4. Silent skips. The runner never posts "still nothing new."
5. Two nudges, one stall message, then silence forever.

---

## 10. What changes at six people

`tech-stack.md` §6.3 already calls Slack-as-interface a known replacement, not a permanent choice. Specifically:

**Dies first:** "one reaction decides an item." With two co-owners who trust each other it is correct. With six it needs quorum per role, and the 2-of-2 admin assumption behind "whoever ran it, the other one ships it" stops resolving to anybody in particular.

**Dies next:** the single `#convo-farm` channel, because six people's convos interleave into soup. Then reading the thread at all — the status roll-up becomes the primary surface rather than a convenience. Then claims that *refuse*, which at six people should queue. Then directive tokens, which start colliding with ordinary chatter once there are enough humans chattering.

**Survives unchanged:** the drop contract and its manifest. Git as the ledger and the commit trailers. The role model — it was written as a permission system precisely so it scales past two. The five gates and what each is for. The reaction vocabulary and the precedence lattice. The wrap seam and the stitcher folder contract. The guest packet.

Notice what breaks: all of it is Slack. None of it is the data model. That is the point of putting the truth in git and treating the thread as a skin. And the migration is already half-built — the guest packet is a web surface on the producer plane, so at six people the *operator* surface becomes the same app, with the reactions becoming buttons that write the same `gates.json`.

---

## 11. Open, not blocking

1. **What goes in `additions[]`.** Owner: Adam. Unblocked by one worked example — pick a convo, write the intro script and one candidate addition, run it through the stitcher, listen to it. Nothing else in this protocol changes when it's answered.
2. **How the outro bump is voiced** — TTS, a recorded template with the number spliced in, or a read take. The protocol guarantees the string and nothing about the performance.
3. **Whether back-catalog convos get a wrap at all.** 098 has a baked-in music bed and a fair-use call already recorded. Whether it gets re-released is editorial, not protocol.
4. **`convo-v1-spec.md` §10 q4 — do guests get told about the checks block in the pitch email.** Not answered here. `briefed_before_recording` is a required field, so the pipeline behaves correctly under either answer and you cannot ship a convo without recording which way it went.
5. **Slack's per-app rate limit on `conversations.replies`.** Newer non-Marketplace apps are limited hard enough that one paginated 30-message thread can cost minutes. Survivable at one to three open convos. It changes the poll design at ten, and it is worth measuring before convo five rather than after.
6. **Where clips and the wrap MP4 live long-term.** `tech-stack.md` §6.4 already flags committing binary media as bloat. Clips stay in the repo for v1 at ~270 KB per convo; the MP4 goes to object storage from day one. The rest follows around convo ten.

---

## 12. Known holes

Three adversarial passes returned **110 findings, 22 blocking**. Full list in
`slack-protocol-audit.json`. These are the ones that change the design rather than patch it:

- **§1.3 (cron */10) + §6.4 ("apply" is a claimed stage) + §3 generally** — The poll is specified only for *drop detection*. Nothing says what advances a convo from stage to stage, when reactions are read, or when the 7-day/18-day/21-day guest timers and the 24h/72h nudges are evaluated. Walking E098: after M01 posts at 09:14 the spec

- **§6.5 ("Slack returns reactions with no timestamps at all… any rule that orders reactions i** — The spec proves reaction times are unavailable to a stateless outbound-only runner, then prints reaction times in two message shapes — one of which (M10) is the split-decision message a human reads to understand who was overruled. An implementer either builds 

- **§1.4 Path A condition 3 ("No file under the drop root missing from files[] — an extra file** — The walked happy path violates its own completeness rule in the thread-root message. E098's archive genuinely contains a file that must be excluded (`…thekerp copy.mp3`, the 2024 re-export with 55 s spliced out, which source.json says must never be transcribed

- **§1.5, §2.6, §3.2–3.6 (every "Lands as" line), §6.6 — `convos/<id>/gates.json`** — `gates.json` is the protocol's central ledger — it holds `client_msg_key`s, every human decision, the `superseded` verb, the `apply_key`, the G4 approval state, and (per the fix above) the Slack read cursor — and it is the one object with no schema. drop.json,

- **§2.4 (v1 delivery is a rendered HTML file an admin emails; the guest replies by email; an ** — In v1 there is no link and no open event, so every guest packet is permanently in the one state that can never resolve — meaning no convo with a guest can ever pass G4 until a human ✅s M16 with an evidence line. Worse, the paste-back path lets an operator writ

- **§8.1–8.3 + M17/M19, checked against /Users/kerp/Dropbox/Zengineering/Claude/stitcher (lib/** — The spec materialises `_wrap/<farm>-<number>/` in the **template** layout (Intro/, Main Convo/, Outro/, Episode Cards/) and then runs `--bare` for E098. Bare mode does not read that layout: `resolve_inputs` requires `episode.{mp4|mp3|wav…}` and `title_card.{pn

- **§8.2, §8.3, M17, M19 — `stitcher --bare` on `_wrap/<farm>-<number>/`** — Bare mode does not read the template folder layout. `stitch.py` routes `--bare` to `resolve_inputs(folder, assets_dir, bare=True)`, which requires `episode.{mp4,mov,mkv,wav,mp3,aif,m4a,flac}` AND `title_card.{png,jpg}` at the TOP of the folder (or `title_card_

- **§8.4 guarantee 1; M17 "Main Convo bytes are sha-identical to the reviewed master"; M19; M2** — Byte-identity is unachievable with the chosen tool, in either mode. Template mode applies `aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo` to `[2:a]` (the main conversation) before `concat=n=5`, then `amix` with the music bed, then `loudnorm=I

- **§8.3 "the music timing math is the stitcher's and is not reimplemented"; M19 reproducibili** — The stitcher's duration source is `ffprobe format.duration` — `lib/probe.py` does `float(fmt.get("duration"))` — which is the exact call `CLAUDE.md` #3-adjacent rules, `convo-v1-spec.md` §4 stage 7, and `source.json.runtime_note` ban outright, and which reads 

- **M18 "upload `_output/098-final.mp3` to Transistor" vs M19/M20 `_output/098-…-final.mp4` vs** — No stage produces an audio file, and the spec names the artifact three different ways. `metadata.EpisodeMeta.output_filename` is hardcoded `f"{slug}-final.mp4"`; every builder ends `-c:v libx264 … -movflags +faststart <path>.mp4`. There is no audio-only path i

- **§8.2/M17/M19 — 098 ships `--bare` with an "Outro bump 11.2 s appended"** — Bare mode cannot append anything. `build_bare_command` takes exactly two inputs — the looped title card and one audio file — and ends with `-shortest`. There is no intro slot, no outro slot, and no concat. So the bump named in M17 and M19 cannot exist in the a

- **§1.4 Path A, condition 3 ("No file under the drop root missing from `files[]`")** — `.DS_Store` permanently and silently blocks every drop made from a Mac. Finder writes it the moment the operator opens the folder to put files in it — which is the only way a synced drop ever happens — and this very repo already carries three of them (`/repo/.

- **§1.4 conditions 3/4/5 and §3.1 M02** — There is no message for "the manifest verifies but a non-file condition blocks adoption." M02 renders rows against `files[]`, so a drop blocked by an extra file, a stray sentinel, or condition 5 produces silence indefinitely. Condition 5 (`now − sealed_at ≥ 12

- **§2.5 resolution table, §3.5 M14/M16 — "Never opened → No. Not ever, on any timer."** — v1 has no open event. §2.4 says the v1 path is "zero new infrastructure": the skill renders `reply-packet.html`, an admin emails it, the guest replies by email. Email attachments and plain links produce no open signal a cron runner can read. So in v1 every gue

- **§2.6 hard blocks; M17 preflight; the named case "someone hand-edits convo.json"** — Nothing binds published content to approved content. Hard block 5 validates `convo.json` against the schema, not against what any human agreed to. A hand-edited claim sentence between G3 and G4 — explicitly forbidden by `CLAUDE.md` line 52 and named as a test 

- **§6 Abandonment vs M17 preflight "G3 ✅ 7/7" — the named case "an admin publishes while an o** — The spec answers this two contradictory ways and never reconciles them. §6 Abandonment: "a half-reviewed gate is a valid state… No gate ever requires completeness to make progress on the part that is decided" — so stage 7 cuts clips and stage 8 renders while b

- **§8.2, §8.3, §8.4, M17, M19 — stitcher mode selection** — `--bare` cannot do what the spec asks. Verified in the tool: `stitch.py --help` says bare "Skips intro/outro segments", and `lib/validator.py:resolve_inputs(..., bare=True)` looks for `episode.{mp4,mp3,wav…}` + `title_card.{png,jpg}` at the TOP of the episode 

- **§5 ("Every apply summary ends with 'read N replies, ignored M'"), M13 ("Everything else ap** — The apply summary is referenced twice as if specified and is never specified. It is also the one message `tech-stack.md` §3 explicitly requires — "The skill reads the thread, applies the decisions, commits, and posts a diff summary" — so a binding rule is sile

- **Whole document — image generation has no stage, no gate and no message** — `tech-stack.md` §2 is a substantial production surface: one style chosen per convo, character renders per person per style, one hero plus 3–5 beat images, a JSON sidecar on every generated image, cost and runtime into provenance, and the rule that **"A new sty

- **M06 queue item 8: "identify b2 20:41 … Rewritten against source.json → structure"** — This re-commits the exact E098 trap it claims to fix. `20:41` is a SESSION/final-mix time (`structure.cold_open.source_range` = 1241.681). The spec's own rule, stated three times, is "every published timestamp is on the master timeline." On the master timeline

- **§1.5 (`drop_id = sha256(sorted (relpath, bytes, sha256) triples)[:12]`) vs §1.3 ("The poll** — The idempotency key is not computable at the moment it is used. §1.5 step 1 checks `drop_id` against the ledger at poll time, before any download, but the key is built from sha256 of every file. On Path A the runner can read declared sha256 out of `drop.json` 


One finding did not survive checking. The stitcher's music timing was called poisoned by
`ffprobe format.duration`, the field measured 5.510 s short on E098's master. `lib/probe.py:40`
does read it — but on the files the stitcher actually processes it is accurate to 8 ms. E098's
master was an unusual CBR file where ffprobe estimated from bitrate. Live only if a
back-catalogue master is ever fed through the stitcher; a decoded-duration fallback in
`probe.py` closes it cheaply.

