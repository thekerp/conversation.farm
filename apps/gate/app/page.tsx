import { NO_ACCESS_MESSAGE, requireReviewer } from '@/lib/auth'
import { BRANCH, CONVO, REPO } from '@/lib/github'
import Review from './review'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>
}) {
  // Server components cannot set cookies, so a stale session is not cleared
  // here — it is cleared by the first API call, which also 403s.
  const auth = await requireReviewer()
  const { error: qsError } = await searchParams
  const error = auth.ok || auth.reason === 'no-session' ? qsError : NO_ACCESS_MESSAGE

  if (!auth.ok) {
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
