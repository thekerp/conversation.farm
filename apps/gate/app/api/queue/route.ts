import { NextResponse } from 'next/server'
import { readSession } from '@/lib/session'
import { BRANCH, CONVO, REPO, getQueue, branchExists } from '@/lib/github'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const s = await readSession()
  if (!s) return NextResponse.json({ error: 'not signed in' }, { status: 401 })

  const url = new URL(req.url)
  const convo = url.searchParams.get('convo') ?? CONVO
  const branch = url.searchParams.get('branch') ?? BRANCH

  try {
    if (!(await branchExists(s.token, branch))) {
      return NextResponse.json({ error: `branch ${branch} does not exist` }, { status: 404 })
    }
    const { doc, sha } = await getQueue(s.token, convo, branch)
    return NextResponse.json({
      doc,
      sha,
      convo,
      branch,
      repo: REPO,
      user: { login: s.login, name: s.name },
    })
  } catch (e: any) {
    return NextResponse.json({ error: e.message ?? 'failed to read queue' }, { status: e.status ?? 500 })
  }
}
