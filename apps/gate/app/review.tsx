'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Patch } from '@/lib/apply'

type Doc = Record<string, any>
type Kind = Patch['kind']

/**
 * Decisions are held here until you submit. One gate is one commit — clicking
 * twelve chips should not write twelve commits, and a half-finished review is
 * not a thing anyone else should see.
 */
export default function Review({ convo, branch, repo }: { convo: string; branch: string; repo: string }) {
  const [doc, setDoc] = useState<Doc | null>(null)
  const [user, setUser] = useState<{ login: string; name: string } | null>(null)
  const [pending, setPending] = useState<Record<string, Patch>>({})
  const [err, setErr] = useState('')
  const [ok, setOk] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setErr('')
    const r = await fetch(`/api/queue?convo=${convo}&branch=${encodeURIComponent(branch)}`)
    const j = await r.json()
    if (!r.ok) return setErr(j.error ?? 'failed to load')
    setDoc(j.doc)
    setUser(j.user)
    setPending({})
  }, [convo, branch])

  useEffect(() => {
    load()
  }, [load])

  const key = (kind: Kind, id: string) => `${kind}:${id}`

  const patch = (kind: Kind, id: string, p: Partial<Patch>) => {
    setOk('')
    setPending((prev) => {
      const k = key(kind, id)
      return { ...prev, [k]: { ...(prev[k] ?? { kind, id }), ...p, kind, id } }
    })
  }

  /** Saved state from the file, overlaid with anything unsubmitted. */
  const view = (kind: Kind, item: any) => {
    const p = pending[key(kind, item.id)]
    const human = { ...(item.human ?? {}), ...(p ?? {}) }
    return {
      decision: (human.decision ?? 'pending') as string,
      note: human.note as string | undefined,
      priority: Boolean(human.priority),
      question: (p?.question ?? item.question) as string,
      dirty: Boolean(p),
    }
  }

  const queue: any[] = doc?.queue ?? []
  const ents: any[] = doc?.entity_candidates?.candidates ?? []
  const gleans: any[] = doc?.gleaning_candidates?.candidates ?? []

  const stats = useMemo(() => {
    const decided = queue.filter((i) => view('queue', i).decision !== 'pending').length
    const live = queue.filter((i) => view('queue', i).decision !== 'cut').length
    return { decided, live, pendingCount: queue.length - decided }
  }, [queue, pending])

  const dirty = Object.keys(pending).length

  async function submit(gate?: { decision: 'approved' | 'changes_requested'; note?: string }) {
    setBusy(true)
    setErr('')
    setOk('')
    const r = await fetch('/api/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ convo, branch, patches: Object.values(pending), gate }),
    })
    const j = await r.json()
    setBusy(false)
    if (!r.ok) return setErr(j.error ?? 'submit failed')
    setOk(`Committed. ${j.pr?.created ? 'Opened' : 'Updated'} PR #${j.pr?.number} — ${j.pr?.url}`)
    await load()
  }

  if (err && !doc) return <main><p className="err">{err}</p></main>
  if (!doc) return <main><p className="pill">loading…</p></main>

  const gate = doc.provenance?.human_gate ?? {}

  const Chips = ({ kind, item, extra }: { kind: Kind; item: any; extra?: React.ReactNode }) => {
    const v = view(kind, item)
    return (
      <>
        <div className="chips">
          <button
            className={`chip ${v.decision === 'approved' ? 'on' : ''}`}
            onClick={() => patch(kind, item.id, { decision: 'approved' })}
          >
            ✅ approve
          </button>
          <button
            className={`chip ${v.decision === 'cut' ? 'on cut' : ''}`}
            onClick={() => patch(kind, item.id, { decision: 'cut' })}
          >
            ✂️ cut
          </button>
          {extra}
          <button
            className={`chip ${v.priority ? 'on' : ''}`}
            onClick={() => patch(kind, item.id, { priority: !v.priority })}
          >
            🔝 first
          </button>
          <button
            className="chip"
            onClick={() => {
              const n = prompt('Note (recorded in the ledger if this is cut):', v.note ?? '')
              if (n !== null) patch(kind, item.id, { note: n })
            }}
          >
            ✍️ note
          </button>
        </div>
        {v.note ? <div className="note">{v.note}</div> : null}
      </>
    )
  }

  return (
    <>
      <header>
        <h1>Gate 1 — {doc.convo}</h1>
        <span className="pill">
          {stats.decided}/{queue.length} decided · {stats.live} would run
        </span>
        {dirty ? <span className="pill bad">{dirty} unsaved</span> : <span className="pill ok">saved</span>}
        <span className="sp" />
        <span className={`pill ${gate.decision === 'approved' ? 'ok' : ''}`}>
          {gate.decision ? `gate: ${gate.decision} · ${gate.by}` : 'gate: open'}
        </span>
        <span className="pill mono">{user?.login}</span>
        <form action="/api/auth/logout" method="post">
          <button className="chip">sign out</button>
        </form>
      </header>

      <main>
        <div className="msg">
          <div className="who">
            <b>convo-farm</b>
            <span className="bot">app</span>
            <time>#convo-farm · thread · writes to {repo}</time>
          </div>
          <h2>{doc.convo} — research queue</h2>
          <p className="sub">
            {queue.length} questions, budget {doc.budget?.target}. Recorded {doc.recorded}. Decisions
            are held here until you submit; one gate is one commit.
          </p>
          {queue.map((it, n) => {
            const v = view('queue', it)
            return (
              <div className={`row ${v.decision === 'cut' ? 'cut' : ''}`} key={it.id}>
                <div className="num">{n + 1}</div>
                <div>
                  <div className="meta">
                    <span className="tag type">{it.type}</span>
                    <span className="tag mono">{it.beat}</span>
                    <span className="tag mono">{it.anchor_label}</span>
                    {it.anchor_outside_window ? <span className="tag">outside clip</span> : null}
                    {it.human?.added_at_gate ? <span className="tag">added by hand</span> : null}
                    {v.dirty ? <span className="tag dirty">unsaved</span> : null}
                    <span className="tag mono">{it.id}</span>
                  </div>
                  <p className="q">{v.question}</p>
                  <details>
                    <summary>why · expected · guards</summary>
                    <div className="body">
                      <p><b>Why.</b> {it.why}</p>
                      <p><b>Expected.</b> {it.expected}</p>
                      {it.guards ? <p><b>Guards.</b> {it.guards}</p> : null}
                      {it.anchor_reason ? <p><b>Anchor.</b> {it.anchor_reason}</p> : null}
                    </div>
                  </details>
                  <Chips
                    kind="queue"
                    item={it}
                    extra={
                      <button
                        className="chip"
                        onClick={() => {
                          const n2 = prompt('Reword. The original is kept in the ledger.', v.question)
                          if (n2 !== null && n2.trim()) patch('queue', it.id, { question: n2 })
                        }}
                      >
                        ✍️ reword
                      </button>
                    }
                  />
                </div>
              </div>
            )
          })}
        </div>

        <div className="msg">
          <div className="who">
            <b>convo-farm</b>
            <span className="bot">app</span>
            <time>entity boxes · orientation, not tendrils</time>
          </div>
          <h2>Reference boxes — pick up to {doc.entity_candidates?.proposed_cap ?? 6}</h2>
          <p className="sub">
            Named on tape, so they get a stored summary and a link instead of a research job. Exempt
            from the three-per-beat and one-domain rules.
          </p>
          <div className="grid">
            {ents.map((e) => (
              <div className={`card ${view('entity', e).decision === 'cut' ? 'cut' : ''}`} key={e.id}>
                <h3>{e.term}</h3>
                <p>
                  <span className="mono">{e.first_label}</span> · {e.why}
                </p>
                <Chips kind="entity" item={e} />
              </div>
            ))}
          </div>
        </div>

        <div className="msg">
          <div className="who">
            <b>convo-farm</b>
            <span className="bot">app</span>
            <time>gleanings · threads to pull</time>
          </div>
          <h2>What the harvest left</h2>
          <p className="sub">
            Places the conversation came up to something and did not close on it. Capped at{' '}
            {doc.gleaning_candidates?.cap ?? 5}; every one quotes the words that came close.
          </p>
          {gleans.map((g) => (
            <div className={`row ${view('gleaning', g).decision === 'cut' ? 'cut' : ''}`} key={g.id}>
              <div className="num">{String(g.kind ?? '?')[0].toUpperCase()}</div>
              <div>
                <div className="meta">
                  <span className="tag type">{g.kind}</span>
                  {g.term ? <span className="tag">never says “{g.term}”</span> : null}
                  <span className="tag mono">{g.label}</span>
                  {g.resolved_by ? (
                    <span className="tag mono">→ {g.resolved_by}</span>
                  ) : (
                    <span className="tag">unrecoverable</span>
                  )}
                </div>
                <p className="q">“{g.quote}”</p>
                <details>
                  <summary>what was in hand</summary>
                  <div className="body">
                    <p>{g.note}</p>
                  </div>
                </details>
                <Chips kind="gleaning" item={g} />
              </div>
            </div>
          ))}
        </div>

        <div className="msg">
          <div className="who">
            <b>convo-farm</b>
            <span className="bot">app</span>
            <time>ledger · what 4a cut before you saw it</time>
          </div>
          <h2>Rejected before you saw it</h2>
          <p className="sub">The machine&rsquo;s half of the funnel. Open it to reinstate something.</p>
          <details>
            <summary>{(doc.decisions?.entries ?? []).length} candidates</summary>
            <table className="ledger">
              <tbody>
                {(doc.decisions?.entries ?? []).map((e: any, i: number) => (
                  <tr key={i}>
                    <td className="mono">
                      {e.fate}
                      <br />
                      <span style={{ opacity: 0.7 }}>{e.reason_code}</span>
                    </td>
                    <td>
                      <b>{e.candidate}</b>
                      <br />
                      <span style={{ color: 'var(--muted)' }}>{e.reason}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </div>
      </main>

      <footer>
        {err ? <span className="err">{err}</span> : null}
        {ok ? <span className="ok">{ok}</span> : null}
        <button className="ghost" disabled={busy || !dirty} onClick={() => submit()}>
          Save {dirty || ''} without closing
        </button>
        <button
          className="ghost"
          disabled={busy}
          onClick={() => {
            const note = prompt('What needs to change?')
            if (note !== null) submit({ decision: 'changes_requested', note })
          }}
        >
          Request changes
        </button>
        <button
          className="go"
          disabled={busy || stats.pendingCount > 0}
          onClick={() => {
            const note = prompt('Approving. Anything to record? (optional)')
            if (note !== null) submit({ decision: 'approved', note })
          }}
        >
          {stats.pendingCount > 0
            ? `${stats.pendingCount} still pending`
            : `Approve ${stats.live} questions & open 4b`}
        </button>
      </footer>
    </>
  )
}
