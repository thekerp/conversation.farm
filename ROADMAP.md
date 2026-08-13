# Roadmap

**Status:** 2026-08-13. One convo in flight, stages 1–3 done.

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
| 3 Segment into beats | **done, unverified** | `beats.v1.json` — 9 beats, repaired after all three passes failed |
| 4 Research pass | not started | needs the beat re-verification first |
| 5 Assemble `convo.json` | not started | |
| 6 Review gate | not started | needs `docs/slack-protocol.md` out of draft |
| 7 Cut clips | not started | 369 s across 9 beats, bounds already snapped to word boundaries |
| 8 Render + commit | not started | fallback renderer does not exist yet |
| 9 Publish gate | not started | |
| 10 Audio out | not started | stitcher hand-off unresolved, see below |

---

## Next three things, in order

**1. Re-verify `beats.v1.json`.** It was repaired after 39 findings and has not been walked again.
Nothing downstream should start until it has. This is the cheapest high-value step left.

**2. Decide the source-timeline question.** Beats carry master-timeline `t`/`t_end` only. E098's b1
is the strongest beat in the episode and its claim lives in cut material that the master timeline
cannot address at all. Either beats gain a source-timeline field, or 87.1 s of real conversation
stays permanently unquotable. This blocks the schema, and the schema blocks stage 5.

**3. Run stage 4 on the nine beats.** `docs/research-pass.md` is the most complete doc in the repo
and has never been executed. Until it runs, there is no evidence the product is a product.

---

## Open decisions

Each of these is waiting on a human, not on work.

| Decision | Why it matters | Owner |
|---|---|---|
| Source-timeline field on beats | Without it the cut material is unaddressable and b1 cannot be fully sourced | Adam + Brian |
| Stitcher bare-mode hand-off | `--bare` cannot append an intro or outro; `build_bare_command` takes exactly two inputs. Byte-identity of the conversation through the tool is also unachievable — every path re-encodes. The episode assembly design depends on resolving this | Brian |
| What gets added on top for RSS | The seam is defined in `docs/slack-protocol.md` §8; the content is deliberately not | Adam |
| Whether guests are told about the checks block before recording | `convo-v1-spec.md` §10 open question 4. The drop contract already carries `briefed_before_recording` as a required field, so it is recorded either way — but the answer changes the pitch email | Adam |
| Renderer | `convo-v1-spec.md` §5 says Brian's call. The fallback renderer ships regardless so nothing waits on it | Brian |

---

## Known debt

- **`docs/slack-protocol.md` is a draft with 22 blocking holes.** Full list in
  `docs/slack-protocol-audit.json`, summary in its §12. The heaviest cluster is the stitcher
  hand-off. Do not build against it as written.
- **`beats.v1.json` is unverified after repair.** See above.
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

---

## Not v1

Accounts on the reader side. Comments. Upvotes. Search. The network. Grafting. Seed exchange. Video.
Any farm but Zengineering. Batch processing the back catalogue. A CMS. See `convo-v1-spec.md` §7.
