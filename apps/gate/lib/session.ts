import { createCipheriv, createDecipheriv, createHmac, randomBytes, timingSafeEqual } from 'node:crypto'
import { cookies } from 'next/headers'

const COOKIE = 'gate_session'
const MAX_AGE = 60 * 60 * 12 // 12h; a review sitting open overnight signs in again

export type Session = {
  token: string   // the reviewer's own GitHub token: it authenticates AND authorises the write
  login: string
  name: string
  exp: number
}

function key(): Buffer {
  const s = process.env.SESSION_SECRET
  if (!s || s.length < 32) {
    throw new Error('SESSION_SECRET must be set to at least 32 characters')
  }
  return createHmac('sha256', 'gate-session-v1').update(s).digest()
}

export function seal(payload: Session): string {
  const iv = randomBytes(12)
  const c = createCipheriv('aes-256-gcm', key(), iv)
  const body = Buffer.concat([c.update(JSON.stringify(payload), 'utf8'), c.final()])
  return [iv, c.getAuthTag(), body].map((b) => b.toString('base64url')).join('.')
}

export function unseal(raw: string): Session | null {
  try {
    const [iv, tag, body] = raw.split('.').map((p) => Buffer.from(p, 'base64url'))
    if (!iv || !tag || !body) return null
    const d = createDecipheriv('aes-256-gcm', key(), iv)
    d.setAuthTag(tag)
    const json = Buffer.concat([d.update(body), d.final()]).toString('utf8')
    const s = JSON.parse(json) as Session
    return s.exp > Date.now() ? s : null
  } catch {
    return null
  }
}

export async function readSession(): Promise<Session | null> {
  const raw = (await cookies()).get(COOKIE)?.value
  return raw ? unseal(raw) : null
}

export async function writeSession(s: Omit<Session, 'exp'>) {
  const store = await cookies()
  store.set(COOKIE, seal({ ...s, exp: Date.now() + MAX_AGE * 1000 }), {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: MAX_AGE,
  })
}

export async function clearSession() {
  ;(await cookies()).set(COOKIE, '', { path: '/', maxAge: 0 })
}

/** OAuth `state`, signed so a forged callback cannot start a session. */
export function signState(): string {
  const nonce = `${Date.now()}.${randomBytes(12).toString('base64url')}`
  const mac = createHmac('sha256', key()).update(nonce).digest('base64url')
  return `${nonce}.${mac}`
}

export function verifyState(state: string | null): boolean {
  if (!state) return false
  const i = state.lastIndexOf('.')
  if (i < 0) return false
  const nonce = state.slice(0, i)
  const got = Buffer.from(state.slice(i + 1))
  const want = Buffer.from(createHmac('sha256', key()).update(nonce).digest('base64url'))
  if (got.length !== want.length || !timingSafeEqual(got, want)) return false
  const ts = Number(nonce.split('.')[0])
  return Number.isFinite(ts) && Date.now() - ts < 10 * 60 * 1000
}
