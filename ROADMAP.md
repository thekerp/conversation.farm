# Roadmap

**Status:** 2026-09-02. One convo in flight, stages 1–3 done and verified — structural pass green, semantic walk run and applied.

v1 is one back-catalogue convo processed end to end and live at a real URL. Everything here is
ordered against that. `docs/convo-v1-spec.md` §6 is the definition of done; this file is where it
stands.

---

## Where E098 is

| Stage | State | Artifact |
|---|---|---|
| 1 Drop | done | `convos/zengineering-098/source.json` |
| 2 Transcribe | done | `transcript.v1.md`, `segments.v1.jsonl` — 451 turns, `confirmed` attribution |
| 2b Cut material | done | `cut-material.v1.md` — 99 s the edit removed, off the isolated tracks |
| 2c Speaker arbitration | done | `speaker-arbitration.v1.json` — 5 turns corrected against the audio |
| 3 Segment into beats | done, verified | `beats.v1.json` — 9 beats; stage 3b green (0 HIGH, 0 MED); semantic walk in `beat-semantic-walk.v1.json`, 19 findings, all applied |
| 4a Extract queue | done, awaiting Gate 1 | `research-queue.v1.json` — 12 questions, verifier green; **not approved, 4b must not run** |
| 4b Research | blocked on Gate 1 + a design fork | one deep-research job per approved question; how it calls a model is undecided, see Open decisions |
| — Gate UI | live | `apps/gate` at <https://gate.conversation.farm>, GitHub sign-in, commits to the convo branch and opens a PR. `tools/gate/serve.py` is the offline equivalent and the reference implementation of the decision rules |
| 5 Assemble `convo.json` | not started | |
| 6 Review gate | not started | needs `docs/slack-protocol.md` out of draft |
| 7 Cut clips | not started | 369 s across 9 beats, bounds already snapped to word boundaries |
| 8 Render + commit | not started | fallback renderer does not exist yet |
| 9 Publish gate | not started | |
| 10 Audio out | not started | stitcher hand-off unresolved, see below |

---

## Next three things, in order

**1. Approve the research queue, then run 4b.** 4a is done: `research-queue.v1.json` holds 12
questions (5 `since`, 4 `verify`, 2 `contradict`, 1 `identify`) covering 8 of 9 beats, and
`skill/stages/stage4a_verify_queue.py` passes it clean. **Gate 1 is open and 4b costs real money,
so nothing runs until a human approves.** Reviewing it is the highest-leverage sixty seconds in the
pipeline (`research-pass.md` §2); the target is under ten minutes.

Review it at **<https://gate.conversation.farm>** — sign in with GitHub, decide, and the app commits
to `convo/zengineering-098-stage4` and updates PR #5. Offline equivalent, no auth, edits the working
tree: `python3 tools/gate/serve.py convos/zengineering-098`.

One standing instruction from the semantic walk: five of its 19 findings were hedge erasure — a
quote or paraphrase rendered stronger than the speaker's hedged version. 4b must treat an unhedged
rendering of a hedged statement as a defect, not a style choice, and never check a stronger claim
than the one made (`beat-semantic-walk.v1.json → outcome`). The queue's `guards` fields carry that
forward per item; the verifier fails the build if a rule-7 guard is dropped.

**2. Assemble `convo.json` (stage 5).** The schema is unblocked — beats carry
`source_t`/`source_t_end` now — but stage 5 has no code. It also needs the research pass's output,
so it lands after item 1.

**3. Build the fallback renderer.** `renderers/fallback/` is empty and stage 8 depends on it.
Python, no deps, no build step, per the layout contract. Nothing about it waits on stages 4–5;
it can proceed in parallel if there's a second pair of hands.

---

## Open decisions

Each of these is waiting on a human, not on work.

| How 4b calls a model | The repo is stdlib-only and has no model-calling code. Either 4b is a stage that calls an API directly (a dependency plus an API key on the runner, which is what `research-pass.md` §7 describes), or it emits one job spec per approved question for an agent to execute and write back (keeps the repo stdlib-only, matches how stages 2–4a already work). Blocks 4b, which blocks 5 | Adam + Brian |
| Decision | Why it matters | Owner |
|---|---|---|
| Stitcher bare-mode hand-off | `--bare` cannot append an intro or outro; `build_bare_command` takes exactly two inputs. Byte-identity of the conversation through the tool is also unachievable — every path re-encodes. The episode assembly design depends on resolving this | Brian |
| What gets added on top for RSS | The seam is defined in `docs/slack-protocol.md` §8; the content is deliberately not | Adam |
| Whether guests are told about the checks block before recording | `convo-v1-spec.md` §10 open question 4. The drop contract already carries `briefed_before_recording` as a required field, so it is recorded either way — but the answer changes the pitch email | Adam |
| Renderer | `convo-v1-spec.md` §5 says Brian's call. The fallback renderer ships regardless so nothing waits on it | Brian |

---

## Known debt

- **`docs/slack-protocol.md` is a draft with 22 blocking holes.** Full list in
  `docs/slack-protocol-audit.json`, summary in its §12. The heaviest cluster is the stitcher
  hand-off. Do not build against it as written.
- **Three segments in `segments.v1.jsonl` have degenerate durations** — `s0061` is 0.00 s
  (`start == end == 555.34`), `s0202` is 0.01 s, `s0376` is 0.03 s. A stage 2 artifact, harmless to
  read but it will divide by zero in anything that computes a rate per segment.
- **`segments.v0.jsonl` has a 600-second duplicated block**, indices 850–1035. It is retained
  deliberately as the cross-ASR diff reference — Scribe's `logprob` finds none of the entity errors
  and diffing against v0 finds all of them — but any reader must drop that range.
- **No renderer, no character sheets, no `convo.json`.** Stages 5, 7 and 8 have no code at all.
- **The archive is 265 MB and 260 MB of it is gitignored audio** that exists in exactly one place.
  `tech-stack.md` §6.4 names repo bloat as the risk; the live risk here is the opposite.

---

## Settled, so nobody relitigates it

- **Music-bed licence.** Called fair use by Adam on 2026-08-13, revisit if the project earns. The
  facts behind it are in `source.json → external_dependency`.
- **Trigger is cloud sync plus a cron pull.** No local watcher — neither laptop is reliably on.
- **Drop contract is transport-agnostic** so a web upload with logins slots in later without the
  protocol caring which transport arrived.
- **`guest` is the consent model**, not a new permission tier. It is the delivery mechanism for
  `tech-stack.md` §2 consent and `convo-v1-spec.md` §3 rule 5 right of reply.
- **"The podcast ships unchanged" is dead.** The conversation is the core and material gets added
  around it on the way to RSS.
- **The cold open gets a beat.** Adam, 2026-08-13.
- **Beats carry optional `source_t`/`source_t_end` in mix/raw-track seconds.** Adam, 2026-09-02.
  Required when a beat quotes material that exists only in cut material; the master↔mix relation is
  `source.json → edit_map`, never a constant offset. The prose `source_timeline_note` escape hatch
  is gone — stage 3b enforces the fields.

---

## Not v1

Accounts on the reader side. Comments. Upvotes. Search. The network. Grafting. Seed exchange. Video.
Any farm but Zengineering. Batch processing the back catalogue. A CMS. See `convo-v1-spec.md` §7.
