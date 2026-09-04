import { clearSession, readSession, type Session } from './session'
import { canPush } from './github'

export type AuthResult =
  | { ok: true; session: Session }
  | { ok: false; reason: 'no-session' | 'no-access' }

/**
 * Push access is re-checked against GitHub on EVERY request, not just at login.
 *
 * A session cookie proves who you are; it does not prove you still have write
 * access. Checking only at sign-in would leave a removed collaborator working
 * for up to the 12-hour cookie lifetime. This costs one API call per request
 * (5,000/hour authenticated, and there are two of us), and it means three
 * things take effect immediately rather than eventually:
 *
 *   - removing someone as a repo collaborator
 *   - that person revoking the OAuth grant on their end
 *   - GitHub invalidating the token for any other reason
 *
 * `clearOnFail` is for route handlers, which are allowed to set cookies.
 * Server components are not, so the page passes it false and simply renders
 * the signed-out view with a reason.
 */
export async function requireReviewer(
  { clearOnFail = false }: { clearOnFail?: boolean } = {},
): Promise<AuthResult> {
  const session = await readSession()
  if (!session) return { ok: false, reason: 'no-session' }

  if (!(await canPush(session.token))) {
    if (clearOnFail) await clearSession()
    return { ok: false, reason: 'no-access' }
  }
  return { ok: true, session }
}

export const NO_ACCESS_MESSAGE =
  'Your push access to the repository has been removed, or the GitHub authorisation was revoked.'
