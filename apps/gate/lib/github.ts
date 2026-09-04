const API = 'https://api.github.com'

export const REPO = process.env.GATE_REPO ?? 'thekerp/conversation.farm'
export const BRANCH = process.env.GATE_BRANCH ?? 'convo/zengineering-098-stage4'
export const CONVO = process.env.GATE_CONVO ?? 'zengineering-098'
export const BASE = process.env.GATE_BASE ?? 'main'

export const queuePath = (convo = CONVO) => `convos/${convo}/research-queue.v1.json`

async function gh(token: string, path: string, init: RequestInit = {}) {
  const r = await fetch(`${API}${path}`, {
    ...init,
    cache: 'no-store',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
      ...(init.headers ?? {}),
    },
  })
  const text = await r.text()
  const body = text ? JSON.parse(text) : null
  if (!r.ok) {
    const msg = body?.message ?? r.statusText
    throw Object.assign(new Error(`GitHub ${r.status}: ${msg}`), { status: r.status, body })
  }
  return body
}

export async function exchangeCode(code: string): Promise<string> {
  const r = await fetch('https://github.com/login/oauth/access_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      client_id: process.env.GITHUB_CLIENT_ID,
      client_secret: process.env.GITHUB_CLIENT_SECRET,
      code,
    }),
  })
  const j = await r.json()
  if (!j.access_token) throw new Error(j.error_description ?? 'no access_token')
  return j.access_token as string
}

export async function whoami(token: string) {
  const u = await gh(token, '/user')
  return { login: u.login as string, name: (u.name ?? u.login) as string }
}

/**
 * Authorisation is repo push access, checked with the reviewer's own token.
 * No user table, no invite flow: if you can push to the repo you can decide,
 * and the commit is attributed to you rather than to a bot.
 */
export async function canPush(token: string): Promise<boolean> {
  try {
    const r = await gh(token, `/repos/${REPO}`)
    return Boolean(r?.permissions?.push)
  } catch {
    return false
  }
}

export async function getQueue(token: string, convo = CONVO, ref = BRANCH) {
  const f = await gh(token, `/repos/${REPO}/contents/${queuePath(convo)}?ref=${encodeURIComponent(ref)}`)
  const json = Buffer.from(f.content, 'base64').toString('utf8')
  return { doc: JSON.parse(json), sha: f.sha as string }
}

/**
 * Optimistic concurrency for free: the sha is a precondition, so if the other
 * reviewer committed while this gate was open GitHub returns 409 and we re-read
 * rather than clobbering them.
 */
export async function putQueue(
  token: string,
  opts: { convo?: string; branch?: string; sha: string; content: string; message: string },
) {
  return gh(token, `/repos/${REPO}/contents/${queuePath(opts.convo ?? CONVO)}`, {
    method: 'PUT',
    body: JSON.stringify({
      message: opts.message,
      content: Buffer.from(opts.content, 'utf8').toString('base64'),
      sha: opts.sha,
      branch: opts.branch ?? BRANCH,
    }),
  })
}

/** The app opens PRs and never pushes to main — CI still publishes on merge. */
export async function findOrCreatePR(token: string, head = BRANCH, base = BASE, title?: string) {
  const owner = REPO.split('/')[0]
  const open = await gh(token, `/repos/${REPO}/pulls?state=open&head=${owner}:${head}`)
  if (Array.isArray(open) && open.length) {
    return { url: open[0].html_url as string, number: open[0].number as number, created: false }
  }
  const pr = await gh(token, `/repos/${REPO}/pulls`, {
    method: 'POST',
    body: JSON.stringify({
      title: title ?? `gate review: ${head}`,
      head,
      base,
      body: 'Opened from the gate review app. Decisions are recorded in the queue file.',
    }),
  })
  return { url: pr.html_url as string, number: pr.number as number, created: true }
}

export async function branchExists(token: string, branch = BRANCH) {
  try {
    await gh(token, `/repos/${REPO}/branches/${encodeURIComponent(branch)}`)
    return true
  } catch {
    return false
  }
}
