/**
 * Decision rules, mirroring tools/gate/serve.py. Both write the same file, so
 * if you change one, change the other — the local tool is the reference
 * implementation and runs against the working tree.
 *
 * Nothing is ever deleted. A cut item keeps its row, stops counting against
 * budget, and stops being structurally validated, because its defects are
 * usually the reason it was cut.
 */
export type Patch = {
  kind: 'queue' | 'entity' | 'gleaning'
  id: string
  decision?: 'approved' | 'cut' | 'pending'
  note?: string
  priority?: boolean
  question?: string
}

type Doc = Record<string, any>

const DECISIONS = new Set(['approved', 'cut', 'pending'])

function bucket(doc: Doc, kind: Patch['kind']): any[] {
  if (kind === 'queue') return doc.queue ?? []
  if (kind === 'entity') return doc.entity_candidates?.candidates ?? []
  return doc.gleaning_candidates?.candidates ?? []
}

export function applyPatch(doc: Doc, p: Patch, by: string, at: string): string | null {
  const items = bucket(doc, p.kind)
  const target = items.find((i) => i.id === p.id)
  if (!target) return `no ${p.kind} item ${p.id}`

  const human = (target.human ??= {})
  if (p.decision !== undefined) {
    if (!DECISIONS.has(p.decision)) return `bad decision ${p.decision}`
    human.decision = p.decision
  }
  if (p.note !== undefined) human.note = p.note
  if (p.priority !== undefined) human.priority = Boolean(p.priority)
  if (p.question !== undefined && p.kind === 'queue') {
    const q = p.question.trim()
    if (q && q !== target.question) {
      human.original_question ??= target.question
      target.question = q
      human.edited = true
    }
  }
  human.by = by
  human.at = at

  // Mirror cuts into the ledger. `item`, not `was`: the row stays in the queue,
  // and `was` would trip the verifier's ledger-contradiction check.
  doc.decisions ??= {}
  const bounced: any[] = (doc.decisions.bounced ??= [])
  const keep = bounced.filter((e) => e.item !== p.id)
  keep.length !== bounced.length && bounced.splice(0, bounced.length, ...keep)
  if (human.decision === 'cut' && !bounced.some((e) => e.item === p.id)) {
    bounced.push({
      item: p.id,
      kind: p.kind,
      candidate: target.question ?? target.term ?? target.note ?? '',
      fate: 'bounced',
      stage: 'gate1',
      reason_code: 'gate1-cut',
      reason: human.note || 'cut at Gate 1 without a note',
      by,
      at,
    })
  }
  return null
}

export function pendingQueue(doc: Doc): string[] {
  return (doc.queue ?? [])
    .filter((i: any) => (i.human?.decision ?? 'pending') === 'pending')
    .map((i: any) => i.id)
}

export function liveQueue(doc: Doc): any[] {
  return (doc.queue ?? []).filter((i: any) => i.human?.decision !== 'cut')
}

export function closeGate(
  doc: Doc,
  gate: { decision: 'approved' | 'changes_requested'; note?: string },
  by: string,
  at: string,
): string | null {
  if (gate.decision === 'approved') {
    const pending = pendingQueue(doc)
    if (pending.length) return `${pending.length} question(s) still pending: ${pending.join(', ')}`
  }
  doc.provenance ??= {}
  doc.provenance.human_gate = {
    decision: gate.decision,
    by,
    note: gate.note || null,
    at,
  }
  return null
}

/** One commit per gate, not per click: a gate is an event, not a stream. */
export function commitMessage(doc: Doc, patches: Patch[], gate: any, convo: string): string {
  const q = patches.filter((p) => p.kind === 'queue')
  const cut = q.filter((p) => p.decision === 'cut').length
  const ok = q.filter((p) => p.decision === 'approved').length
  const ents = patches.filter((p) => p.kind === 'entity' && p.decision === 'approved').length
  const gleans = patches.filter((p) => p.kind === 'gleaning' && p.decision === 'approved').length
  const head =
    gate?.decision === 'approved'
      ? `gate1(${convo}): approved ${ok}, cut ${cut}`
      : gate?.decision === 'changes_requested'
        ? `gate1(${convo}): changes requested`
        : `gate1(${convo}): ${q.length} decision(s) recorded`
  const parts = [
    `${liveQueue(doc).length} questions would run.`,
    ents ? `${ents} entity box(es) approved.` : '',
    gleans ? `${gleans} gleaning(s) approved.` : '',
    gate?.note ? `\nNote: ${gate.note}` : '',
  ].filter(Boolean)
  return `${head}\n\n${parts.join(' ')}`.trim()
}
