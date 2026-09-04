import { NextResponse } from 'next/server'
import { readSession } from '@/lib/session'
import { BASE, BRANCH, CONVO, findOrCreatePR, getQueue, putQueue } from '@/lib/github'
import { applyPatch, closeGate, commitMessage, liveQueue, type Patch } from '@/lib/apply'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  const s = await readSession()
  if (!s) return NextResponse.json({ error: 'not signed in' }, { status: 401 })

  const body = await req.json().catch(() => null)
  if (!body) return NextResponse.json({ error: 'bad json' }, { status: 400 })

  const convo: string = body.convo ?? CONVO
  const branch: string = body.branch ?? BRANCH
  const patches: Patch[] = Array.isArray(body.patches) ? body.patches : []
  const gate = body.gate ?? null
  if (!patches.length && !gate) {
    return NextResponse.json({ error: 'nothing to submit' }, { status: 400 })
  }

  const at = new Date().toISOString().slice(0, 10)

  try {
    // Re-read at submit time and apply on top. The sha we then write with is the
    // one we just read, so a concurrent commit by the other reviewer makes GitHub
    // reject this with 409 instead of silently clobbering them.
    const { doc, sha } = await getQueue(s.token, convo, branch)

    for (const p of patches) {
      const err = applyPatch(doc, p, s.login, at)
      if (err) return NextResponse.json({ error: err }, { status: 400 })
    }
    if (gate) {
      const err = closeGate(doc, gate, s.login, at)
      if (err) return NextResponse.json({ error: err }, { status: 400 })
    }

    const content = JSON.stringify(doc, null, 2) + '\n'
    const message = commitMessage(doc, patches, gate, convo)

    let commit
    try {
      commit = await putQueue(s.token, { convo, branch, sha, content, message })
    } catch (e: any) {
      if (e.status === 409 || e.status === 422) {
        return NextResponse.json(
          { error: 'someone else committed while you were reviewing — reload and reapply', conflict: true },
          { status: 409 },
        )
      }
      throw e
    }

    // The app opens a PR and never pushes to main. CI publishes on merge, and
    // the verifier runs on the PR, so a gate cannot land a queue the stage rejects.
    const pr = await findOrCreatePR(s.token, branch, BASE, `gate review: ${convo}`)

    return NextResponse.json({
      ok: true,
      commit: commit?.commit?.html_url ?? null,
      pr,
      live: liveQueue(doc).length,
      gate: doc.provenance?.human_gate ?? null,
    })
  } catch (e: any) {
    return NextResponse.json({ error: e.message ?? 'submit failed' }, { status: e.status ?? 500 })
  }
}
