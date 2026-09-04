import { NextResponse } from 'next/server'
import { signState } from '@/lib/session'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(req: Request) {
  const id = process.env.GITHUB_CLIENT_ID
  if (!id) return NextResponse.json({ error: 'GITHUB_CLIENT_ID is not set' }, { status: 500 })

  const origin = new URL(req.url).origin
  const u = new URL('https://github.com/login/oauth/authorize')
  u.searchParams.set('client_id', id)
  u.searchParams.set('redirect_uri', `${origin}/api/auth/callback`)
  // The repo is public, so public_repo is enough to commit. Least privilege:
  // this token must never be able to touch a private repo.
  u.searchParams.set('scope', 'public_repo')
  u.searchParams.set('state', signState())
  return NextResponse.redirect(u.toString())
}
