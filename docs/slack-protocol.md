# The harvest thread — Slack protocol

**Addendum to:** `convo-v1-spec.md` §4, `tech-stack.md` §3, `research-pass.md` §2
**Status:** draft, 2026-08-13
**Scope:** what the production skill posts to `#convo-farm` and what the two operators do back, from
the moment files land to the moment a page and an episode are live.

---

## 0. The shape of it

Two operators — Adam and Brian. Both install the same skill. Neither is the one who runs it. Both
have day jobs and small children, so decisions arrive hours apart, out of order, and either may
abandon a review halfway through.

Three properties make that survivable, and everything below is a consequence of them:

1. **The skill never blocks on a human, and a human never waits on a model.** Every gate is a set of
   independent per-object decisions. Reacting to 3 of 7 beats is a valid, committed state.
2. **Git is the truth, Slack is the interface** — applied literally. Claims, drops and decisions are
   git refs and committed files. Slack is the human-visible mirror. If they disagree, git wins and
   the skill posts a correction.
3. **Every message shows its work.** Run id, stage, actor, model, cost, runtime and commit on every
   single message the skill posts. No exceptions. This project publishes a block admitting where it
   was wrong; the thread holds the same standard.

### A fourth plane: the porch

`tech-stack.md` §0 defines three planes — reader, data, producer. Auth (§3 below) and manual upload
(§1 below) need an authenticated web surface, which none of the three can be without breaking. So:

| Plane | What it is | Rule |
|---|---|---|
| **Reader** | The convo page | Static. Unchanged. |
| **Data** | The repo | Git. Unchanged. |
| **Producer** | The skill + the cron runner | Unchanged. |
| **Porch** | Upload, log-in, the guest review page | **Never serves a convo page. A convo page never calls it.** |

That one rule keeps the performance tenet intact. The porch is where humans who are not in Slack
touch the pipeline.

---

## 1. The drop contract

### 1.1 Canonical shape

A **drop** is a directory. Not a file, not a Slack upload, not a link. One directory per convo.

```
<drop-root>/<farm>/<number>/
  drop.json              the manifest — the only file the runner reads first
  master/                the published or mastered audio (0 or 1 file)
  tracks/                per-speaker audio, named by person id: adam.mp3, tbj.mp3, guest-<id>.mp3
  transcripts/           vendor transcripts as delivered (riverside.txt, scribe-raw.json, …)
  session/               optional edit session / project archive (.sesx, …)
  notes/                 optional human notes, corrections, guest contacts, hand-written edit map
```

**The runner never writes into a drop.** It reads and it leaves it alone — the same rule
`source.json` already states for the E098 archive. Consumption is recorded as a git ref, not as a
moved file, because moving files inside a syncing folder is how you lose them.

### 1.2 `drop.json`

```json
{
  "schema": "drop/1",
  "farm": "zengineering",
  "number": 98,
  "title": "On Open Source Collaboration",
  "recorded": "2020-08-22",
  "transport": "synced-folder",
  "submitted_by": "adam",
  "submitted_at": "2026-08-14T03:07:41Z",
  "manifest": "authored",
  "manifest_tool": "farm drop 0.3.1",

  "participants": [
    { "person": "adam", "role": "host",  "track": "tracks/adam.mp3" },
    { "person": "tbj",  "role": "host",  "track": "tracks/tbj.mp3" },
    { "person": "guest-jsmith", "role": "guest", "track": "tracks/guest-jsmith.mp3",
      "contact": "j@example.com", "reply_window_hours": 72 }
  ],

  "master": { "file": "master/098.mp3", "timeline": "master" },
  "master_is_an_edit": true,
  "master_to_source": "session/098.sesx",

  "files": [
    { "path": "master/098.mp3", "bytes": 58971648, "sha256": "9c41…a7", "role": "master" },
    { "path": "tracks/adam.mp3", "bytes": 60214784, "sha256": "1be0…3d", "role": "track" }
  ]
}
```

**The contract in one sentence:** a drop is a directory whose `drop.json` names every file with its
exact byte length and sha256, declares which timeline the master is on, and declares whether the
master is an edit of the session.

Anything that can produce that directory is a valid transport. The protocol does not care which
arrived and has no branch on `transport` anywhere — the field exists for provenance only.

| Transport | Who writes `drop.json` | Who hashes |
|---|---|---|
| Synced folder | `farm drop <dir>`, run locally by the operator at drop time | the local skill |
| Web upload (the porch, not built) | the upload handler on upload completion | the server |
| Anything later (a recorder that uploads directly) | that thing | that thing |

A local one-shot command at drop time is not a local watcher. The rejected thing was a daemon on a
laptop that is not reliably on. The human is at the machine at the moment they drop the files;
running one command there is free.

### 1.3 Two things the E098 audit forces into the contract

**`master_is_an_edit` is required and is enforced, not trusted.**
098's master is 8 clips of the session with 87.1 s of conversation cut and a cold open moved from
20:41 to the front. Master and session diverge by up to 83.4 s and no single offset relates them.

- `true` → `master_to_source` must resolve to a session file the runner can parse, or a hand-written
  `notes/edit-map.json` with the same `clips[] {master_in, master_out, mix_in, mix_out}` shape.
  Missing → **the drop is rejected at intake with a named reason.** It is not harvested badly.
- `false` → the runner verifies it by decoded length and refuses again if master and session differ
  beyond 200 ms.
- Every published timestamp is on the **master** timeline (`convo-v1-spec.md` §9).

**Duration is never read from `ffprobe format.duration`.**
On 098 it reads 5.510 s short. The intake message publishes both numbers side by side so the
discrepancy is visible rather than silently absorbed.

Input is getting cleaner — an auto-cleaned track plus matching transcripts, eventually from our own
recorder — but the contract does not assume master and session are the same recording, ever.

---

## 2. Trigger: cloud sync plus a cron pull

No local watcher. Files land in a synced folder; the stateless cloud runner
(`research-pass.md` §7) polls, sees a complete drop, and opens the thread.

### 2.1 Interval

`*/10 * * * *` — **every 10 minutes.** A poll is a directory listing plus a hash of anything whose
size or mtime changed; it costs approximately nothing. Nobody is waiting, so 10 minutes bounds the
worst case "I dropped it and went to bed" latency at 10 minutes for a manifested drop and 30 for an
unmanifested one.

### 2.2 Completeness — the 60 MB-track-mid-sync problem

This is the obvious bug and the manifest is the answer to it. **A partially synced file cannot hash
correctly.** Size alone is not enough; sha256 is definitive.

**Path A — manifested.** `drop.json` present and parses; every listed file present at exactly the
listed byte length and exactly the listed sha256; no extra unlisted files in `master/` or `tracks/`.
That is COMPLETE, on the first verifying poll. No quiescence window needed, because the hash already
proves every byte arrived.

**Path B — unmanifested.** Someone dragged files in without running `farm drop`. Require **three
consecutive polls, ≥20 minutes apart end to end**, with an identical file set, sizes and mtimes. The
runner synthesizes a manifest, marks it `"manifest": "synthesized"`, and says so out loud in the
thread and in the published provenance. Stage 7 refuses to cut clips until a human answers
`master_is_an_edit`.

**Guards on both paths:**
- Never harvest a directory containing a sync placeholder: `*.icloud`, `*.partial`, `*.tmp`,
  `*.crdownload`, `~$*`, `.~lock.*`, or any zero-byte file listed in the manifest with non-zero bytes.
- Never harvest a directory whose newest mtime is under 120 s old.
- A file that fails its hash is **not an error.** It is a file still syncing. Stay silent, retry next
  poll. Only after 3 consecutive failures spanning ≥30 minutes post one message, then go quiet for an
  hour. Anti-noise is a hard rule: a cron that cries wolf every 10 minutes gets muted, and a muted
  channel is a dead protocol.

### 2.3 Idempotency

`drop_id` = first 12 hex of `sha256` over the canonical manifest — the sorted list of
`(path, bytes, sha256)` triples. Content-addressed, so the same bytes always produce the same id and
different bytes always produce a different one.

The claim is a **git ref**, created atomically:

```
git push origin <commit>:refs/harvest/drops/<drop_id>
```

Non-fast-forward pushes to an existing ref are rejected by default. That is a compare-and-swap on the
remote with no new infrastructure and no new source of truth. If the push is rejected, another runner
already owns this drop — exit 0, post nothing.

Two-phase, so a crash between claim and thread cannot lose or duplicate a convo:

1. Push the claim ref. Its commit holds `{drop_id, claimed_at, runner, thread_ts: null}`.
2. Open the Slack thread, then force-update the ref with `thread_ts` filled in.

A claim older than 30 minutes with `thread_ts: null` is dead and the next poll takes it over — the
same 30-minute expiry `tech-stack.md` §3 already defines for stage claims.

**Re-drops.** A corrected or extended drop hashes differently, so it is a new `drop_id`. If the convo
already has an open thread, the new drop posts into that thread, diffs the two manifests, and re-runs
only the stages whose inputs changed. Gate decisions survive, because they are keyed to beat ids and
research ids, not to the drop.

---

## 3. Roles, which are also the consent model

`tech-stack.md` §2 says guests are opt-in, default to no likeness, and `consent.generative: false` is
honored with no override flag. `convo-v1-spec.md` §3 rule 5 says guests are checked by the same
standard as hosts and get a right of reply before publication.

**The auth role and the consent model are the same object seen twice.** So they live in the same
file. `people/<id>.json` already carries `character.consent`; roles go next to it:

```json
{
  "schema": "person/1",
  "id": "guest-jsmith",
  "name": "Jamie Smith",
  "roles": ["guest"],
  "auth": { "slack_user_id": null, "email": "j@example.com" },
  "character": {
    "consent": { "generative": false, "updated": "2026-08-15" }
  },
  "rights": {
    "reply_window_hours": 72,
    "reply_window_extendable_by": ["operator", "admin"],
    "reply_window_waivable_by": []
  }
}
```

One record per person: who they are, what they consented to, and what they can do. Every role change
is a commit, like every other decision.

### 3.1 The three roles

| Role | Is | Authenticates via |
|---|---|---|
| **admin** | Adam and Brian, both | Slack workspace identity |
| **operator** | anyone with the skill installed and a Slack identity in `#convo-farm` | Slack OIDC on the porch — same identity, no second password store |
| **guest** | a participant who is not an operator and is not in the channel | a signed single-purpose capability URL. No account, ever. |

Plus **runner**, a machine identity with no approval power at all. It posts, it commits, it opens
PRs. It holds a Slack token and model keys, no deploy key, **and no merge right.**

### 3.2 What each can do at each gate

| Gate | admin | operator | guest | runner |
|---|---|---|---|---|
| Intake | reject a drop, force-expire a claim | re-drop, fix and re-drop | — | verify, open thread, or reject |
| 4a research queue | react, reply | react, reply | — | post, apply, commit |
| 4b research results | react, reply | react, reply | — | post, apply, commit |
| 6 beat review | react; may clear another operator's ✂️ **only with a stated reason, which commits** | react and reply on any object | — | post, apply, commit |
| Right of reply | may extend the window; **may not waive or shorten it** | may extend the window | reply, set consent, request a cut | send, mirror, enforce |
| 9 publish | ✅ / 🚫; may set the quiet window to 0 with a stated reason | ✅ / 🚫 | 🚫 by proxy — a dispute posts a block operators must clear | open the PR |
| Merge | — | — | — | — |

**Merging is nobody's manual privilege and is not the runner's.** The runner writes the approval
state into `decisions.jsonl` and onto the PR. A GitHub Actions workflow — in CI, holding the merge
right the runner does not have — merges when the rule is satisfied. `research-pass.md` §7's one
sentence survives: the runner can never publish.

**Admin is the highest process authority and has zero authority over consent.** That is the sentence
the role model exists to make true. An admin can force a claim, reject a drop, override a process
gate, and change the role table. An admin cannot flip `consent.generative`, cannot waive a guest's
right-of-reply window, and cannot shorten it. There is no flag.

### 3.3 Who can approve a publish

Publish needs **one operator ✅ and no 🚫**, then either:

- a **second operator ✅**, which merges immediately, or
- a **quiet window** with no 🚫 — default **12 hours**, set per repo in `farm.config.json`.

That is the answer to two operators with day jobs. A solo operator can ship, but only after the other
has had half a day to object, and the thread does the waiting via a scheduled message rather than a
human remembering. A single 🚫 stops the timer until whoever placed it removes it.

**With a guest on the convo, publish is blocked until the reply window closes or the guest signs
off,** regardless of how many operators approved. No admin flag skips it.

### 3.4 How a guest's right of reply actually reaches them

The guest is not in Slack and never will be. So:

1. At assembly the runner emails the guest a **capability URL** — signed, single-purpose, 72 h
   default, revocable and re-issuable by an admin (a new link invalidates the old). Scope: read this
   convo's guest view, write this guest's own replies and consent flag. Nothing else. No account, no
   password, no session that outlives the window.
2. The page is on the **porch**, not the reader plane. It shows: the guest's beats, every check that
   quotes them, a preview of the page as it stands, and two controls — a reply box per check, and a
   likeness-consent switch that is **off** by default.
3. What happens to each action:

| Guest action | Effect |
|---|---|
| Replies to a check | Ships verbatim as `host_note` on that check. Auto-honored. Operators cannot edit it. |
| Leaves likeness consent off | Nothing generates a likeness. Typographic card. Auto-honored, permanently, no override. |
| Turns likeness consent on, later off | Honored both ways; turning it off triggers a re-render. |
| Requests a passage be cut | **Not** auto-honored. Opens a gate in the thread with the guest's reason attached; an operator decides on the record and the reason commits. |
| Does nothing until the window closes | Publishes with `right_of_reply: {offered, responded: null, closed}` printed on the page. |

Two different defaults, deliberately: **consent defaults closed and never opens without action; the
right of reply defaults offered and closes on a timer.** A silent guest cannot block the convo
forever, and a silent guest also never acquires a cartoon likeness.

4. Guest activity is **mirrored into the thread** by the runner so operators see the state without
   leaving Slack. The mirror is one-way; nothing an operator types reaches the guest.

---

## 4. One reaction vocabulary

`tech-stack.md` §3 and `research-pass.md` §2 conflict: ⚠️ means "this check is unfair, pull it" in
one and "promote this to a check" in the other.

**Kept: `tech-stack.md` §3's set** — ✅ ✂️ 🔁 🔎 🔒 — because it attaches to the durable objects
(beats, checks) and it is the doc that defines the Slack protocol at all.

**Renamed / resolved:**

| Emoji | Was | Is now | Why |
|---|---|---|---|
| ⚠️ | tech-stack: "this check is unfair, pull it" | **research-pass's meaning wins: "this belongs in the checks block"** | Pulling an unfair check is just ✂️ on that check's message. The old meaning was redundant, so the emoji was free. |
| ✍️ | research-pass: "add a question" | **"my threaded reply is the content"** | Adding a question and rewriting a claim are the same act — supplying text in a reply. One verb. |
| 🔝 | research-pass: "prioritize" | **"this survives a budget trim"** | "Do it first" means nothing when 8 jobs run in parallel. "Keep this one if we cut" means something. |
| 🚫 | — | **new: "block"** | The publish gate needs a stop that is not a cut. |

### The table. Each emoji means exactly one thing everywhere.

| Emoji | Verb | Means, on any object, at any gate |
|---|---|---|
| ✅ | `approve` | Take this as written. |
| ✂️ | `cut` | Remove it. It never ships. On a claim message, releases the claim. |
| 🔁 | `redo` | Regenerate this one. The skill reads your threaded reply for what to change. |
| 🔎 | `dig` | Not enough here. Spend more — more sources, deeper model, another pass. Costs money. |
| ⚠️ | `check` | This belongs in the checks block. Verify the claim and publish the verdict. |
| 🔝 | `first` | Do not cut this one if the budget runs out. |
| ✍️ | `author` | My threaded reply is the text. Add it, or use it instead of yours. |
| 🔒 | `lock` | Frozen. Later stages may not touch it. |
| 🚫 | `block` | Stop. Nothing ships past this until whoever placed it removes it. |

Nine verbs, total, for the whole pipeline.

**Coverage check.** Gate 4a: ✅ 🔝 ✂️ ✍️. Gate 4b: ✅ ⚠️ ✂️ 🔁 🔎. Gate 6: ✅ ✂️ 🔁 🔎 ⚠️ 🔒 ✍️.
Gate 9: ✅ 🚫. Claims: ✂️.

**Precedence, because decisions arrive hours apart and out of order.** Reactions are applied in
Slack-timestamp order, not arrival order, and then resolved:

1. 🚫 beats everything.
2. ✂️ beats ✅. Destructive beats permissive, because the objector is asleep and cannot argue.
3. Only the person who placed a ✂️ removes it — or an admin, with a reason that commits.
4. 🔒 beats everything except 🚫.
5. Removing your own reaction withdraws the decision, as long as the stage has not run.

**An unknown emoji is ignored, and tallied.** Three uses of the same unlisted emoji gets one message
asking for it to be added to the table or dropped. A vocabulary that quietly accretes private
meanings is a vocabulary that has stopped working.

### Where free text is read

A reaction cannot carry an argument. So, mechanically:

**The skill parses a message only when all four hold:** it is a threaded reply in the convo thread; it
is from an operator or admin; it replies to (or is posted after) a message whose footer says
`reads replies`; and it begins with a recognized directive line. Everything else in the thread is
human conversation. It is archived with the convo and never parsed.

Grammar, deliberately tiny — one directive per line:

```
<object-id>: <verb> <free text>
```

`<object-id>` is an id the message printed — `b3`, `r07`, `t12`, `c02`, or a queue number.
`<verb>` is one of the nine above, plus `note`, which attaches free text without changing state and
commits as `human.note`.

```
b5: redo make it about the licence, not the patent
4: first
7: cut
add: verify — did the FSF ever respond to the Tesla pledge?
c02: note boring but it proves the block isn't only self-flagellation
```

**A reaction and a reply on the same object: the reaction sets the state, the reply supplies the
content.** 🔁 plus a reply is redo-with-instructions.

**An unparsed line is echoed back once**, verbatim, as "not parsed." A human never silently loses an
instruction.

---

## 5. Every decision lands as a commit

| Gate | Written to | Commit message |
|---|---|---|
| Intake | `convos/<id>/drop.json` (copied), `source.json` | `intake(zengineering-098): drop 4f2a9c1b7e03 — 11 files verified` |
| 4a queue | `research.json` → `queue[].human` | `gate4a(zengineering-098): 8 approved, 1 cut, 1 added — adam` |
| 4b results | `research.json` → `items[].human` (`research-pass.md` §4) | `gate4b(zengineering-098): 6 tendril, 2 check, 1 dropped — adam,tbj` |
| 6 beats | `convo.json` → `beats[]`, `checks[]`, `tendrils[]` | `gate6(zengineering-098): cut b2 b3, redo b5, dig b6 — adam,tbj` |
| Guest | `people/<guest>.json`, `convo.json` → `checks[].host_note` | `guest(zengineering-101): reply on c04, consent unchanged — guest-jsmith` |
| 9 publish | PR approval state + `decisions.jsonl` | `gate9(zengineering-098): approved — adam` |
| Role change | `people/<id>.json` → `roles` | `roles: grant operator to tbj — adam` |

Two artifacts per convo carry the audit, both append-only:

- **`convos/<id>/decisions.jsonl`** — one line per human decision:
  `{ts, slack_ts, actor, role, object, verb, reply_text, resulting_commit}`.
- **`convos/<id>/ledger.jsonl`** — one line per model call:
  `{run_id, stage, model, input_tokens, output_tokens, cost_usd, runtime_s, prompt_sha, output_sha}`.

Together with `provenance` in `convo.json`, those two files are how someone in six months
reconstructs why each beat and each check exists.

**If Slack is down**, the skill writes the message it would have posted to
`convos/<id>/outbox/<ts>.json` and commits it. A later run flushes the outbox. The thread never loses
an event, because the thread was never the record.

---

## 6. Message anatomy

Every message the skill posts has the same three parts.

**Header** — one line, object id first, so a scrolled thread is scannable:
`<emoji> *<object id>* · <one-line identity>`

**Body** — Slack Block Kit. `section` for prose, `fields` for paired facts, `context` for the
provenance footer, an attachment colour rail for verdicts (green `confirmed`, amber `off` /
`contested` / `outdated`, red `wrong`, grey `unverified`). `actions` buttons **only** where a reaction
cannot work: a link to the preview, the PR, the guest link. `unfurl_links: false` everywhere.

**Footer** — a `context` block, small grey text, on every message with no exceptions:

```
run f4a2 · stage 4b research · runner · claude-opus-4.6 deep-research · $0.9200 · 184 s · commit c02d5a1 · reads replies
```

Zero-model stages print `no model calls · $0.0000`. The `reads replies` token is load-bearing: it is
the only thing that makes a reply parseable.

**The canvas** is pinned to the thread and holds all mutable state, updated in place and never
reposted. That is what lets the messages be pure events — nothing is ever edited to say "actually now
it's at stage 8," so scrollback stays a true record of what was known when.

**Clips are uploaded as Slack files** in the thread, so a beat can be heard without leaving. A 15 s
Opus mono clip is ~60 KB (`tech-stack.md` §1).

---

## 7. The messages

Verbatim. `<angle brackets>` are substitutions.

### 7.1 Intake — thread root

```
:seedling: *zengineering-098 — "On Open Source Collaboration"*
Drop `d/4f2a9c1b7e03` complete. Opening the harvest.

*What landed* — 11 files, 412.7 MB, manifest authored by `farm drop 0.3.1`, submitted by adam
• master/098.mp3 — 58.9 MB — sha `9c41…a7` — timeline: *master*
• tracks/adam.mp3 — 60.2 MB — sha `1be0…3d`
• tracks/tbj.mp3 — 60.2 MB — sha `77aa…19`
• transcripts/scribe-raw.json — 4.1 MB — sha `0d3c…8e`
• session/098.sesx — 1.2 MB — sha `bb90…c4`
…and 6 more. Full manifest in the canvas.

*Timeline audit*
• `master_is_an_edit: true` → edit map resolved from `session/098.sesx` ✅ 8 clips, 6 internal cuts
• master decoded length *3683.239 s* (140999 frames × 1152 ÷ 44100)
  `ffprobe format.duration` says 3677.729 — 5.510 s short. Ignored, as always.
• session 3761.058 s. Master is 77.8 s shorter, and no single offset relates them.
• Every published timestamp will be on the *master* timeline.

*Participants* adam (host, operator) · tbj (host, operator). No guests.
*Branch* `convo/zengineering-098` · *Drop ref* `refs/harvest/drops/4f2a9c1b7e03`

Next: stage 2, transcribe. Nobody needs to do anything yet.
```
```
run f4a2 · stage 1 intake · runner · no model calls · $0.0000 · 4.1 s · commit 3e91b0c
```

### 7.2 Intake — rejected

```
:octagonal_sign: *zengineering-099 — drop rejected at intake*
Drop `d/91cc0e22a5f1` verified clean — 9 files, every hash matches. Not harvesting it.

*Why* `drop.json` says `master_is_an_edit: true` and `master_to_source: null`.
The master is an edit of the session and nothing in the drop relates the two timelines. A beat
published at 20:41 would point at the wrong twenty minutes. E098 taught us this the expensive way:
a single offset between master and session is wrong by up to 83.4 s.

*To unblock, any one of*
1. Put the edit session in `session/` and re-run `farm drop` — the map comes out of it.
2. Write `notes/edit-map.json` by hand:
   `{"clips":[{"master_in":0.0,"master_out":12.084,"mix_in":1241.681,"mix_out":1253.765}, …]}`
3. Set `master_is_an_edit: false` — only if the master really is the unedited session. I verify
   that by decoded length and will refuse again if it isn't.

Nothing was harvested. Re-drop with a fix; the drop ref releases on the next poll.
```

### 7.3 Intake — unmanifested drop

```
:warning: *Unmanifested drop* — `zengineering/099/` has no `drop.json`.
Harvesting it anyway: 9 files, byte-identical across 3 polls over 22 minutes, no partial-sync markers.
Manifest *synthesized* by the runner from what was on disk.

*What that costs* no submitter identity, no declared participants, no `master_is_an_edit`, no
independent hashes to check the sync against. Provenance on the published page will say
`manifest: synthesized`.

*What I'm assuming* master = the only file in `master/`, timeline = master, master_is_an_edit =
*unknown*. Stage 7 will refuse to cut clips until someone answers that.

*Cheap fix* run `farm drop <drop-root>/zengineering/099` on the machine that dropped it. I'll pick
up the real manifest on the next poll and keep everything already done.
```

### 7.4 Drop stuck mid-sync

Posted at most once per drop, then silence for an hour.

```
:warning: *A drop in `zengineering/098/` isn't finishing.*
First seen 03:12 UTC. 3 verification failures over 32 minutes.

`tracks/tbj.mp3` — manifest says 60,214,784 bytes / sha `77aa…19`. On disk: 41,238,528 bytes.
That is a file still syncing, not a bad file. Nothing has been harvested and nothing is wrong yet.

Going quiet for an hour. If it's still short then, the sync is stuck and it's worth looking at the
machine that dropped it.
```

### 7.5 Re-drop

```
:package: *Re-drop* — `d/8e1f0b334c92` supersedes `d/4f2a9c1b7e03` on zengineering-098.
*Changed* `transcripts/riverside.txt` — new file
*Unchanged* 10 of 11, including `master/098.mp3` (same sha), so nothing is re-transcribed.

Stages 2, 3, 4a and 4b are unaffected and will *not* re-run. Stage 5 re-assembles to pick up the new
reference transcript. Gate 6 decisions are kept — they key to beat ids, not to the drop.
Convo spend is unchanged at $7.31.
```

### 7.6 Claim

```
:lock: *claim* — `stage 4b research` on zengineering-098 by *runner* (cron)
ref `refs/harvest/claims/zengineering-098/4b` · expires 15:41 UTC, 30 min
✂️ this message to release it early.
```

### 7.7 Claim expired

```
:unlock: *Claim expired* — `stage 4b` on zengineering-098, held by runner since 15:11.
30 minutes, no commit. Released.

Last commit on the branch is `c02d5a1` — r01–r04 written, r05–r08 not. Stage 4b is idempotent:
the next run redoes r05–r08 and leaves r01–r04 alone. Cron retakes it at :40. Nothing to do.
```

### 7.8 Stage 2 complete — transcribe

```
:white_check_mark: *stage 2 — transcribe* · zengineering-098
451 turns · 11,742 words · speaker_confidence *confirmed*

*Method* per-track audio ownership, arbitrated per turn against the isolated tracks.
• 249 turns confirmed by audio · 5 reassigned against the diarizer, margins 6.6–19.1 dB
• 75 left to diarization as genuinely simultaneous speech · 122 too short or unmapped to score
• median separation 38.19 dB across 170 turns; wrong-offset controls at chance, so the alignment
  is not an artifact of the scoring

*What we do not know* nothing in the audio proves which human is on which file. The mapping rests on
the filename token `thekerp` plus `source.json`. If the recorder wrote the per-guest files under
swapped handles, this inverts and no test run here can see it. That sentence ships in provenance.

*Defects carried forward* 293 zero-duration words (2.49%), clustered in overlap — clip bounds snap
to the nearest word with duration > 0 and pad 250 ms. 6 glued tokens flagged so the extractor
doesn't promote `importantIf` to a proper noun.

*Cross-check* vs Riverside, joined by text not timestamp: 5 entity disagreements, listed in the canvas.

`transcript.v1.md` · `segments.v1.jsonl`
```
```
run f4a2 · stage 2 transcribe · runner · elevenlabs-scribe · $0.4100 · 214 s · commit 8ab30f2
```

### 7.9 Gate 4a — the research queue

One message, numbered, per `research-pass.md` §2.

```
:mag: *Gate 1 of 2 — approve the research queue* · zengineering-098
9 questions out of stage 4a. Running all 9 costs about *$6.30* and ~11 minutes wall clock.
Nothing runs until this is approved. Budget for reading this: 3 minutes.

1. `verify` · b2 09:15 — "Tesla has open sourced all of their patents." True as stated?
2. `verify` · b4 34:52 — Git written by Linus Torvalds, who also created Linux.
3. `since` · b3 21:26 — Apple's closed App Store vs Android's openness. What changed since 2020?
4. `since` · b6 45:33 — "Almost everything has an open source counterpart." Still true in 2026?
5. `contradict` · b5 38:12 — Adam: Git's append-only model should go everywhere. Best objection?
6. `enrich` · b4 34:52 — Best account of why Git was written, past the Torvalds trivia.
7. `since` · b7 52:41 — the blockchain-adjacent aside. What happened to that thesis?
8. `identify` · b1 — the licences they gesture at without naming.
9. `since` · b5 27:10 — Heartbleed as the "many eyes" counterexample. Where does that argument stand?

:warning: *#8's beat is the cold open — audio lifted from 20:41 and moved to the front.*
I wrote the question against `structure.cold_open.source_range` (session 1241.7–1253.8), not against
t=0. Flagging it because it is exactly the trap in `research-pass.md` §5.

3 of 9 are `since`, which is the right shape for a six-year-old convo.

*React here* ✅ run it as written · 🔝 keep these if we trim the budget
*Or reply, one directive per line*
```
> b5: redo …   4: first   7: cut   add: verify — did the FSF respond to the Tesla pledge?
```
```
run f4a2 · stage 4a extract · runner · claude-haiku-4.6 · $0.1200 · 31 s · commit d92f110 · reads replies
```

### 7.10 Queue approved, 4b launched

```
:rocket: *Queue approved — 4b running* · zengineering-098
adam ✅ 15:02. 8 running, 1 cut (#7, adam ✂️ "blockchain aside"), 1 added (#10, adam ✍️
"did the FSF respond to the Tesla pledge?").

Forecast *$5.80 ± $1.20*, 8 parallel jobs, ETA ~11 min. Convo spend so far $0.53.
Results post one message each. Nobody waits.
```

### 7.11 Gate 4b — one message per result

Green rail. Decision makeable from the first three lines; everything under them is for the person who
wants it and for the reader six months out.

```
:mag: *r04* · `since` · beat b6 45:33 · verdict *outdated* · confidence *medium* · 4 sources
> "Almost everything has an open source counterpart."  — tbj, 2020-08-22

*What we found* Half-vindicated, half-inverted, which is more interesting than either. The 2020
trend line broke in two directions at once: several major projects relicensed away from
OSI-approved terms (HashiCorp → BUSL 2023, Redis → RSALv2/SSPL 2024, Elastic → SSPL 2021 then
back to AGPL 2024), and separately open-*weight* AI models arrived and changed what "an open source
counterpart" even denotes.

*Why not high confidence* the relicensing wave is well documented; the claim's scope — "almost
everything" — was never precise enough to falsify cleanly. That goes on the page rather than getting
rounded up.

*Sources* — 4, all fetched, all 200 at 15:31 UTC, 4 distinct domains
• HashiCorp — "HashiCorp adopts Business Source License" · 2023-08-10 · hashicorp.com
• Redis — "Redis Adopts Dual Source-Available Licensing" · 2024-03-20 · redis.io
• Elastic — "Elasticsearch is Open Source, Again" · 2024-08-29 · elastic.co
• OSI — "The Open Source AI Definition 1.0" · 2024-10-28 · opensource.org
✅ `since` rule satisfied — every source published after the 2020-08-22 recording date.

*Default destination* one tendril and one check on b6.
✅ take it · ⚠️ checks block only · ✂️ drop · 🔁 rerun, say what to change in a reply · 🔎 dig deeper
```
```
run f4a2 · stage 4b · runner · claude-opus-4.6 deep-research · $0.9200 · 184 s · 41 pages fetched · commit c02d5a1 · reads replies
```

A thin one, so the ✂️-without-discussion case has a shape too. Grey rail.

```
:mag: *r06* · `enrich` · beat b4 34:52 · verdict *n/a* · confidence *low* · 1 source
> Best account of why Git was written, past the Torvalds trivia.

*What we found* One usable link: the 2007 Google Tech Talk. Everything else that came back was a
restatement of the Wikipedia article, which `research-pass.md` §3 rule 2 says is a show note, not a
tendril.

*Why low* one source, and it's the obvious one. This does not clear rule 4 — nothing here is
non-obvious.

*Sources* — 1, fetched, 200 at 15:33 UTC
• Google Tech Talks — "Linus Torvalds on git" · 2007-05-03 · youtube.com

*Recommendation* ✂️. b4 already has 2 tendrils and one of them is non-obvious. This one costs a
domain slot for nothing.
✅ take it anyway · ✂️ drop · 🔁 rerun with a narrower question · 🔎 dig deeper (+$0.70)
```
```
run f4a2 · stage 4b · runner · claude-opus-4.6 deep-research · $0.3100 · 71 s · 9 pages fetched · commit c02d5a1 · reads replies
```

### 7.12 Gate 6 — one message per beat

Clip uploaded as a file on the same message.

```
:seedling: *b4* · 34:52 · *tbj* · speaker `confirmed`, 12.8 dB margin · beat 4 of 7
> "Git was written by Linus Torvalds — the same guy who wrote Linux — because he needed a version
> control system for the kernel and nothing that existed was good enough."

*Claim, as we'd publish it*
Git exists because Linus Torvalds needed kernel version control and rejected everything available.

*Clip* `clips/b4.mp3` · 34:52 → 35:19 · 27 s · 108 KB, opus mono
bounds snapped to words with duration > 0, padded 250 ms, 4.1 s clear of the nearest edit boundary

*Tendrils* — 2, both already ✅ at gate 4b, shown for context only
• `t09` video — Linus's 2007 Google Tech Talk on Git — youtube.com
  "him explaining the design decisions in his own words, badly and at length"  ← the non-obvious one
• `t10` article — "A Short History of Git", Pro Git — git-scm.com

*Checks* — 1, already ✅ at gate 4b
• `c02` `confirmed` high — Torvalds wrote both. Sourced.

*You are deciding the beat, not the research.* The tendrils and checks above passed gate 4b; leave
them alone unless the beat itself changes what they should be.
✅ ship it · ✂️ cut the beat · 🔁 rewrite the claim, say how in a reply · 🔎 tendrils are weak
⚠️ there's a claim of fact here we didn't check · 🔒 lock it
```
```
run f4a2 · stage 5 assemble · runner · claude-sonnet-4.6 · $0.0800 · 12 s · commit 4b7c902 · reads replies
```

### 7.13 Gate 6 applied — partial

The message that makes abandoning a review halfway safe.

```
:pencil: *Gate 6 applied — partial* · zengineering-098
Read 11 reactions and 2 replies, ts 15:41 → 22:07, applied in timestamp order.

• b1 ✅ adam → kept
• b2 ✂️ tbj → cut. 8 → 7 beats.
• b3 ✅ adam, ✂️ tbj → *cut*. ✂️ beats ✅; tbj placed it, so tbj or an admin removes it. 7 → 6.
• b4 ✅ adam ✅ tbj → kept, both
• b5 🔁 adam + "make it about the licence, not the patent" → rewritten, reposted below as *b5 v2*
• b6 🔎 tbj → back to 4b as one `enrich` question, +$0.70 forecast
• b7 — no reaction. Gate stays open on b7 only.

*The whole remaining ask is b7 and b5 v2.* Nothing else is waiting on either of you.
Commit `f0a91c3` · beats 8 → 6, +1 pending · convo spend $7.31 · human time so far 13 min
```

### 7.14 Superseded reaction

```
:arrows_counterclockwise: *Your ✅ landed on b5 v1, which no longer exists.*
b5 was rewritten at 22:07 (🔁 adam) and reposted as *b5 v2*. Reactions on superseded versions are
ignored so a stale approval can't ship. Re-react on v2 — it's three messages down.
```

### 7.15 Guest — right of reply sent

```
:envelope: *Guest right of reply sent* · zengineering-101 · `guest-jsmith` (Jamie Smith)
Emailed j@example.com at 09:14 UTC. Single-use link, expires *2026-08-17 09:14 UTC*, 72 h.

*What Jamie sees* their 3 beats, the 2 checks that quote them, a preview of the page, a reply box per
check, and one likeness-consent switch — currently *off*, which is the default and stays the default.

*What happens to what they do*
• A reply → ships verbatim as `host_note` on that check. We can't edit it.
• Consent left off → nothing generates a likeness. Typographic card. No override flag exists, and
  admin does not have one.
• A removal request → does *not* auto-apply. It opens a gate here with Jamie's reason attached and
  one of us decides on the record.
• Silence → the window closes and we publish with
  `right_of_reply: {offered: 2026-08-14, responded: null, closed: 2026-08-17}` printed on the page.

Publish is blocked until the window closes or Jamie signs off. The publish card already carries 🚫.
```

### 7.16 Guest — activity mirror

```
:speech_balloon: *Guest activity* · guest-jsmith · 2026-08-15 21:33 UTC
• `c04` — replied. Ships verbatim, commit `77b1e0a`:
  > "I said 'roughly a third' and I'd stand by that, but I was talking about seats, not revenue.
  > The check is comparing me to a revenue number."
• likeness consent — left *off*. Typographic card confirmed.
• removal requests — none.

⚠️ c04 now carries a reply that says we measured the wrong thing. Worth deciding whether the check
is right before publish. React on the c04 message above.
1 of 2 guest checks answered · window closes 2026-08-17 09:14 UTC
```

### 7.17 Build failure — dead tendril

```
:x: *Build failed — dead tendril* · zengineering-098 · stage 8
`t11` https://blog.example.com/2019/the-post → *404* at 09:02 UTC.
It was 200 at 15:31 on 2026-08-14. It died between research and build.

The build fails on this by design — `convo-v1-spec.md` §6, `CLAUDE.md` #3. A dead link on a page
whose premise is self-fact-checking is the worst available bug.

t11 is back at the gate. b6 keeps 2 tendrils either way, which is above the floor.
✂️ drop it · 🔁 find a replacement, +$0.70 · ✍️ reply with a URL and I'll use it if it returns 200
```

### 7.18 Spend checkpoint

```
:heavy_dollar_sign: *Spend checkpoint* — zengineering-098 crossed $10.00, now at $10.54.
63 model calls across 4 stages. Biggest single call: r04 deep research, $0.92, 184 s, 41 pages.
No cap is set, so this is a notice and not a stop. Set one: `farm budget zengineering-098 15`.
```

### 7.19 Gate 9 — publish

One card, both artifacts. See §8 for why the episode is here and not at stage 10.

```
:package: *Gate 2 of 2 — publish* · zengineering-098
Everything is built. This approves the page *and* the episode in one go. Budget: 3 minutes.

*The page* https://preview.conversation.farm/zengineering/98
6 beats · 14 tendrils, all fetched, all 200 at build, 14 distinct domains · 5 checks
(2 confirmed · 1 off · 1 outdated · 1 unverified) · 2 seeds
38.2 KB HTML gz · 11.4 KB critical CSS · zero render-blocking JS · LCP 0.81 s Slow 4G · CLS 0.004
total weight with every lazy asset *1.71 MB* of the 2 MB budget

*The episode* `_output/098-on-open-source-collaboration-final.mp4` · 62:41 · [preview]
Intro/ standing recorded intro v3, 0:34 → 7 s gap → *Main Convo/ the reviewed master, byte-identical*
→ 7 s gap → Outro/ auto bump v1, 0:19 · music bed 22 s mark landing in both gaps
conversation integrity r = 0.99998 over 3683.2 s against the reviewed master ✅
the bump says: "Everything we got wrong, plus where to go next, is at
conversation dot farm slash zengineering slash ninety-eight."

*Spend* $9.84 — transcribe 0.41 · extract 0.12 · research 7.94 · images 1.12 · render 0.25
*Human* 24 decisions, 2 gates, 31 minutes total across both of you
*PR* #14 `convo/zengineering-098` → `main`. Merging is what publishes. CI merges; I can't.

adam ✅ at 22:14. A second ✅ opens it immediately.
Otherwise it merges automatically at *2026-08-16 10:14 UTC* — 12 h quiet window.
✅ approve · 🚫 block, which stops the timer until you remove it
```

### 7.20 Quiet-window countdown

Posted as a Slack scheduled message at approval time, so the thread does the waiting.

```
:hourglass_flowing_sand: *zengineering-098 publishes in 1 hour* — 2026-08-16 10:14 UTC.
One approval (adam), no blocks, no guest window. 🚫 on the publish card stops it.
No action means it ships.
```

### 7.21 Published

```
:tada: *Live* — https://conversation.farm/zengineering/98
PR #14 merged by CI at 10:14 UTC, deployed in 41 s. The runner held no key; it never does.

6 beats · 5 checks, 3 of them not `confirmed` · 14 tendrils, zero fabricated, all re-fetched in CI
and all 200 · full transcript in Dirt.
Episode `098-on-open-source-collaboration-final.mp4` handed to Transistor. RSS updated 10:19.

The old show notes for this episode were four links. The committed record of what it took to beat
that: `decisions.jsonl` — 24 decisions · `ledger.jsonl` — 63 model calls, $9.84 · `provenance` in
`convo.json`.

Thread closed. 🔁 on this message reopens it.
```

### 7.22 The canvas

Pinned to the thread. Updated in place, never reposted.

```
zengineering-098 · On Open Source Collaboration
state reviewed · branch convo/zengineering-098 · PR #14 · drop d/4f2a9c1b7e03

STAGE            STATUS     BY        WHEN         COMMIT
1  intake        done       runner    08-14 03:12  3e91b0c
2  transcribe    done       runner    08-14 03:19  8ab30f2
3  segment       done       runner    08-14 03:24  a71c4e9
4a extract       done       runner    08-14 03:26  d92f110
   gate 4a       approved   adam      08-14 15:02  5c0be21
4b research      done       runner    08-14 15:34  c02d5a1
   gate 4b       approved   adam,tbj  08-14 22:07  e13aa07
5  assemble      done       runner    08-14 22:11  4b7c902
   gate 6        partial    adam,tbj  08-15 09:40  f0a91c3   ← b7 undecided
7  clips         done       runner    08-15 09:52  91de0aa
8  render+stitch done       runner    08-15 10:07  bd2f731
   gate 9        1 of 2     adam      08-15 22:14  —
10 audio out     waiting    —         —            —

SPEND  $9.84   transcribe 0.41 · extract 0.12 · research 7.94 · images 1.12 · render 0.25
HUMAN  31 min  gate4a 4 · gate4b 12 · gate6 13 · gate9 2
OPEN   b7 undecided · guests none · blocks none · quiet window closes 08-16 10:14 UTC
FILES  manifest 11 · decisions.jsonl 24 · ledger.jsonl 63 calls · full manifest below
```

---

## 8. The RSS seam, and where the stitcher sits

### 8.1 The seam

The raw conversation is the core. Material is added around it on the way out to RSS. What that
material is has not been decided, and this protocol does not decide it.

**The seam is named `wrap/`,** and it is deliberately the same shape the stitcher already takes:

```
convos/<id>/wrap/
  intro/          the standing recorded intro — where this conversation came from
  outro/          the auto-generated bump pointing at the page
  cards/          episode cards, 16:9 and 1:1
  music/          the bed (Zengineering Intro Tune w-Fade.mp3 for 103+)
```

`main-convo/` is not in `wrap/`. It is the reviewed master, untouched.

### 8.2 What the protocol guarantees at the seam

1. **The conversation inside the shipped episode is byte-identical to the reviewed master.** No
   re-encode, no edit, no insertion inside it. Additions are strictly around it. This is machine
   checked, the same way `source.json` verified 098's clips: correlation over the main-convo span
   must be ≥ 0.999, and the publish card prints the number.
2. **Exactly two slots exist: before and after.** No mid-roll, no third slot, in v1. Needing a third
   changes this document, not a config file.
3. **The outro bump URL is deterministic and knowable before the audio ships** —
   `conversation.farm/<farm>/<number>` — so the episode can be fully rendered before the publish
   gate rather than promised at it.
4. **Nothing enters `wrap/` without passing the publish gate**, because the gate approves the
   rendered episode, not a plan for one.

### 8.3 What is deliberately open

**What else goes in the wrap is undecided and this document does not invent an answer.** Candidates
that have been said out loud but not chosen: a cold open lifted from a beat, a spoken "here's what we
got wrong" segment reading the checks block, a sponsor read, chapter markers, a different intro per
farm.

- **Owner of the decision:** Adam.
- **What unblocks it:** one worked example — pick a real convo, write the intro script and one
  candidate addition, run it through the stitcher, listen to it.
- **What changes when it's decided:** `wrap/intro/` and `wrap/outro/` gain content and possibly
  sub-slots. Guarantees 1 and 2 above do not move. The publish card grows lines. No other part of
  this protocol changes, which is the point of naming the seam before filling it.

### 8.4 Where the hand-off sits, and which gate covers it

`convo-v1-spec.md` §4 puts audio at stage 10, human, "unchanged from today." That line is dead — the
podcast does not ship unchanged.

**Proposed amendment: the stitcher runs at stage 8, alongside the render.** Stage 8 becomes
*render + stitch + commit*. Stage 9's publish card carries the page and the episode. Stage 10 becomes
*upload the approved master to Transistor* — mechanical, post-gate, automatable later without adding
a gate.

Why: the URL is deterministic, so the outro bump can be generated before publish; therefore the
episode can be finished before publish; therefore the publish gate can approve a real artifact.
**A gate on a promised artifact is not a gate.** This keeps the count at two human gates, exactly as
§4 requires.

The stitcher call, template mode, from the existing tool at
`/Users/kerp/Dropbox/Zengineering/Claude/stitcher`:

```
uv run python stitch.py convos/<id>/ --template
```

`gap_seconds: 7`, `music_sync_seconds: 22` — the 22 s mark of the bed lands at the midpoint of each
gap. Both the timing math and its 26 passing tests are the stitcher's, not ours, and the protocol
does not reimplement them. It supplies a folder in the shape the stitcher documents and reads back
one MP4.

---

## 9. Concurrency

`tech-stack.md` §3 already gives the durable lock — a branch per convo — plus claims with a
30-minute expiry. Four extensions make it work for two people deciding hours apart.

1. **Claims are per (convo, stage), not per convo.** Reviewing beats does not block a research run.
2. **Reacting never needs a claim.** Gates are read-only. *Applying* decisions is itself a claimed
   stage called `apply`, so simultaneous reactions are fine and only the write is serialized.
3. **A claim is a git ref, not a Slack message.** `refs/harvest/claims/<convo>/<stage>`, created with
   the same create-only push as a drop claim. The Slack message is the mirror. Git wins on
   disagreement and the skill posts a correction.
4. **The runner claims like a human.** Cron holds no special path. A human running the skill at the
   same moment as cron gets refused, or refuses cron, by the same rule.

**Out-of-order decisions.** Applied in Slack-timestamp order, not arrival order, then resolved by the
precedence rules in §4. Last-writer-wins per (object, actor); across actors, destructive beats
permissive.

**Abandonment.** A claim with no commit after 30 minutes expires with one notice. A half-reviewed
gate is a valid state: decisions are per-object and independent, so the skill applies what it has and
leaves the gate open on the rest. **No gate ever requires completeness to make progress on the part
that is decided.**

**Idempotency of apply.** `apply_key` = hash of the set of `(object, actor, verb, slack_ts)` tuples
read. If HEAD already carries that key, exit 0. Re-running against an unchanged thread is a no-op,
which means a crashed apply is safe to re-run blind.

---

## 10. Failure modes

| # | Failure | What happens |
|---|---|---|
| 1 | 60 MB track syncing when cron fires | sha256 mismatch. Silent retry. One message after 3 failures / 30 min, then quiet for an hour. §7.4 |
| 2 | Files dropped with no manifest | Path B: 3 stable polls, synthesized manifest, degraded provenance said out loud and printed on the page. §7.3 |
| 3 | Master is an edit, no map | Rejected at intake with the three ways to fix it. Nothing half-harvested. §7.2 |
| 4 | `ffprobe format.duration` | Never used for a bound. Intake prints it next to the decoded length so the 5.5 s gap is visible. |
| 5 | Two runners see one drop | Create-only ref push. Loser exits 0, posts nothing. |
| 6 | Runner crashes mid-stage | Claim expires in 30 min, one notice naming the last commit and what is and isn't written. Stage is idempotent. §7.7 |
| 7 | Reaction on a superseded message | Ignored, and the actor is told which version to re-react on. §7.14 |
| 8 | Tendril 200 at research, 404 at build | Build fails by design. Tendril returns to the gate with three ways out. §7.17 |
| 9 | Guest never responds | Window closes, convo publishes, page prints `responded: null`. Consent stays off forever regardless. |
| 10 | Slack down or token expired | Messages queue in `convos/<id>/outbox/` as commits, flushed on the next run. The thread was never the record. |
| 11 | Unknown emoji | Ignored and tallied. Three uses gets one message asking to add it or stop. |
| 12 | Both operators approve opposite things | Precedence in §4: 🚫 > ✂️ > 🔒 > ✅, applied in Slack-ts order, with the conflict named in the apply summary. §7.13 |

---

## 11. Human minutes

| Gate | Messages | Budget | What it costs if segmentation is good |
|---|---|---|---|
| 4a queue | 1 | 3 min | one ✅ |
| 4b results | 8–10 | 6 min | ~40 s each; the first three lines carry the decision |
| 6 beats | 6–9 | 8 min | mostly single ✅; one or two 🔁 with a reply |
| 9 publish | 1 | 3 min | one ✅, or ✅ and a 12 h wait |
| **Total** | | **20 min** | split across two people, no contiguous block over ~8 min |

`research-pass.md` §6 caps the two research gates at 10 combined; 3 + 6 fits. Gate 6's 8 minutes is
the number to watch — if it goes past that, segmentation is bad and segmentation is the thing to fix,
not the reviewer's patience.

Everything below the first three lines of any message is for the person who wants it and for whoever
reads this thread in six months. It is not in the 20 minutes.

---

## 12. What changes at six people

`tech-stack.md` §6.3: Slack-as-interface works for two and badly for six. It is a known replacement,
not a permanent choice. When it goes:

**Survives unchanged, because none of it is a Slack object:** the drop contract, `drop.json`, the
drop-id and ref-based idempotency, the nine verbs, `decisions.jsonl`, `ledger.jsonl`, the provenance
footer's contents, the role model in `people/<id>.json`, the guest capability link, the wrap seam,
the two gates.

**Breaks first:**
1. **Approval attribution.** "One ✅ plus a quiet window" means "nobody looked" at six people. Replace
   with role-scoped required-N approvals.
2. **Thread scroll.** 40 messages is fine for two and unreadable for six. The canvas becomes the
   primary surface and the messages become notifications.
3. **Claim contention.** Per-(convo, stage) claims are enough for two, not for six sharing a convo.
   Needs per-object leases.
4. **Reaction ambiguity.** With two people, "someone ✂️'d it" identifies a person. With six it needs a
   UI that shows who and why without hovering.

**The replacement:** the porch, already required by D2 and D3, grows a queue view. Slack becomes
notification-only. Approvals move to the web app where they can be role-scoped, required-N, and
audited. Because the verbs and the decision log already live in git rather than in Slack, that
migration is a new front end over an unchanged record — which is the entire reason the vocabulary is
in the repo and not in a Slack workflow.
