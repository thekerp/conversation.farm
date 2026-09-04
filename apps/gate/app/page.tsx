import { readSession } from '@/lib/session'
import { BRANCH, CONVO, REPO } from '@/lib/github'
import Review from './review'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>
}) {
  const s = await readSession()
  const { error } = await searchParams

  if (!s) {
    return (
      <div className="signin">
        <h1>Gate review</h1>
        <p>
          Sign in with GitHub. Decisions are committed to <code>{REPO}</code> as you, on{' '}
          <code>{BRANCH}</code>, and land through a pull request — this app never pushes to main and
          holds no deploy key.
        </p>
        {error ? <p className="err">{error}</p> : null}
        <a className="btn" href="/api/auth/login">
          Sign in with GitHub
        </a>
      </div>
    )
  }

  return <Review convo={CONVO} branch={BRANCH} repo={REPO} />
}
