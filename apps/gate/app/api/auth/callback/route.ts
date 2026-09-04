import { NextResponse } from 'next/server'
import { verifyState, writeSession } from '@/lib/session'
import { canPush, exchangeCode, whoami, REPO } from '@/lib/github'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const url = new URL(req.url)
  const code = url.searchParams.get('code')
  const state = url.searchParams.get('state')

  if (!verifyState(state)) {
    return NextResponse.redirect(`${url.origin}/?error=${encodeURIComponent('bad or expired state')}`)
  }
  if (!code) {
    return NextResponse.redirect(`${url.origin}/?error=${encodeURIComponent('no code')}`)
  }

  try {
    const token = await exchangeCode(code)
    const { login, name } = await whoami(token)

    // Authorisation is push access on the repo, nothing else. Someone who
    // cannot push cannot decide, and the check uses their own token.
    if (!(await canPush(token))) {
      return NextResponse.redirect(
        `${url.origin}/?error=${encodeURIComponent(`${login} has no push access to ${REPO}`)}`,
      )
    }

    await writeSession({ token, login, name })
    return NextResponse.redirect(url.origin)
  } catch (e: any) {
    return NextResponse.redirect(`${url.origin}/?error=${encodeURIComponent(e.message ?? 'auth failed')}`)
  }
}
