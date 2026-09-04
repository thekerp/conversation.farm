import { NextResponse } from 'next/server'
import { NO_ACCESS_MESSAGE, requireReviewer } from '@/lib/auth'
import { BRANCH, CONVO, REPO, getQueue, branchExists } from '@/lib/github'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const auth = await requireReviewer({ clearOnFail: true })
  if (!auth.ok) {
    return auth.reason === 'no-access'
      ? NextResponse.json({ error: NO_ACCESS_MESSAGE }, { status: 403 })
      : NextResponse.json({ error: 'not signed in' }, { status: 401 })
  }
  const s = auth.session

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
