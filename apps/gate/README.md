# Gate review app

The review gates from `docs/research-pass.md` §2, hosted, for Adam and Brian.

**The queue file in git is the source of truth. This app edits it.** It is not a
database in front of the pipeline — it reads `convos/<id>/research-queue.v1.json`
from a branch, applies your decisions, and commits back. That is deliberate: the
product is auditability, and a decision that lives only in a mutable row has no
history a reader or a future stage can inspect.

## What it guarantees

- **Never pushes to `main`.** It commits to the convo branch and opens a PR. CI
  publishes on merge, so CLAUDE.md non-negotiable 6 holds: the app has no deploy key.
- **Never runs the stages.** It is JS; the verifiers are Python. So the guarantee
  moves to CI — `.github/workflows/verify.yml` runs `stage3b_verify_beats.py` and
  `stage4a_verify_queue.py` on every PR touching `convos/`. A gate decision cannot
  land a queue the stage rejects, because the PR goes red.
- **One gate is one commit.** Decisions are held in the browser until you submit,
  so twelve clicks are one commit with a readable message, not twelve.
- **Optimistic concurrency.** Writes carry the file's SHA as a precondition. If
  the other reviewer committed while your gate was open, GitHub returns 409 and
  you reload rather than silently clobbering them.
- **Identity is GitHub, authorisation is push access.** No user table, no invite
  flow. Commits are attributed to the human who made the decision, so the ledger's
  `by:` is verifiable rather than a config default. Scope is `public_repo` only.

## Setup

Deploy first (to learn the URL), then create the OAuth app against it, then set
env vars and redeploy. The callback needs a real URL, hence the order.

1. **Create the Vercel project** with **root directory `apps/gate`**, separate
   from the site project. Note the deployment URL.
2. **Create a GitHub OAuth app** at <https://github.com/settings/developers>:
   - Homepage: your deployment URL
   - Authorization callback URL: `<deployment URL>/api/auth/callback`
3. **Set env vars** on the project:

   | Variable | Value |
   |---|---|
   | `GITHUB_CLIENT_ID` | from the OAuth app |
   | `GITHUB_CLIENT_SECRET` | from the OAuth app |
   | `SESSION_SECRET` | 40+ random chars — `openssl rand -base64 32` |
   | `GATE_REPO` | `thekerp/conversation.farm` (default) |
   | `GATE_BRANCH` | branch holding the queue, e.g. `convo/zengineering-098-stage4` |
   | `GATE_CONVO` | `zengineering-098` (default) |
   | `GATE_BASE` | `main` (default) |

4. Redeploy.

Add the callback for `http://localhost:3000/api/auth/callback` to the same OAuth
app if you want `npm run dev` to work.

## Local, without any of that

`tools/gate/serve.py` is the offline version. Stdlib Python, no auth, edits the
working tree directly, and runs the real verifier after every write:

```
python3 tools/gate/serve.py convos/zengineering-098
```

It is also the reference implementation of the decision rules — `lib/apply.ts`
mirrors it. **Change one, change the other.**
