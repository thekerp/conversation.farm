#!/usr/bin/env python3
"""Gate review UI. The queue file is the source of truth; this edits it.

    python3 tools/gate/serve.py convos/zengineering-098

Then open http://127.0.0.1:8765. Every click writes research-queue.v1.json
atomically and re-runs stage4a_verify_queue.py, so the UI cannot leave the file
in a state the stage would reject without showing you.

Stdlib only, no build step, binds loopback only. Same constraints as the
fallback renderer: if it needs npm it does not belong in this repo.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERIFIER = ROOT / "skill" / "stages" / "stage4a_verify_queue.py"

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("convo_dir", type=Path)
ap.add_argument("--port", type=int, default=8765)
ap.add_argument("--user", default="adam", help="who the decisions are recorded as")
args = ap.parse_args()

CONVO = args.convo_dir.expanduser().resolve()
QUEUE = CONVO / "research-queue.v1.json"
if not QUEUE.is_file():
    sys.exit(f"no research-queue.v1.json under {CONVO}")

DECISIONS = {"approved", "cut", "pending"}


def load():
    return json.loads(QUEUE.read_text(encoding="utf-8"))


def save(doc):
    """Atomic: a half-written source of truth is worse than none."""
    fd, tmp = tempfile.mkstemp(dir=str(CONVO), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, QUEUE)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def verify():
    r = subprocess.run([sys.executable, str(VERIFIER), str(CONVO)],
                       capture_output=True, text=True)
    return {"exit": r.returncode, "out": r.stdout + r.stderr}


def buckets(doc):
    return {
        "queue": doc.get("queue", []),
        "entity": (doc.get("entity_candidates") or {}).get("candidates", []),
        "gleaning": (doc.get("gleaning_candidates") or {}).get("candidates", []),
    }


def state():
    doc = load()
    beats = json.loads((CONVO / "beats.v1.json").read_text(encoding="utf-8"))["beats"]
    return {"doc": doc, "verify": verify(), "user": args.user,
            "beats": [b["id"] for b in beats]}


def apply_decision(doc, kind, item_id, body):
    items = buckets(doc).get(kind)
    if items is None:
        return f"unknown kind {kind!r}"
    target = next((i for i in items if i.get("id") == item_id), None)
    if target is None:
        return f"no {kind} item {item_id!r}"

    human = target.setdefault("human", {})
    if "decision" in body:
        if body["decision"] not in DECISIONS:
            return f"bad decision {body['decision']!r}"
        human["decision"] = body["decision"]
    if "note" in body:
        human["note"] = body["note"]
    if "priority" in body:
        human["priority"] = bool(body["priority"])
    if "question" in body and kind == "queue":
        # An edited question is a different question. Keep the original so the
        # ledger can show what the machine proposed against what shipped.
        if body["question"].strip() and body["question"] != target.get("question"):
            human.setdefault("original_question", target.get("question"))
            target["question"] = body["question"]
            human["edited"] = True
    human["by"] = args.user
    human["at"] = date.today().isoformat()

    # Mirror cuts into the ledger. `item`, not `was` -- the row stays in the
    # queue so nothing is lost, and `was` would trip the ledger-contradiction
    # check in the verifier.
    ledger = doc.setdefault("decisions", {}).setdefault("bounced", [])
    ledger[:] = [e for e in ledger if e.get("item") != item_id]
    if human.get("decision") == "cut":
        ledger.append({
            "item": item_id, "kind": kind,
            "candidate": target.get("question") or target.get("term") or target.get("note", ""),
            "fate": "bounced", "stage": "gate1", "reason_code": "gate1-cut",
            "reason": human.get("note") or "cut at Gate 1 without a note",
            "by": args.user, "at": human["at"],
        })
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/api/state":
            return self._send(200, state())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "bad json"})

        doc = load()
        if path == "/api/decision":
            err = apply_decision(doc, body.get("kind"), body.get("id"), body)
            if err:
                return self._send(400, {"error": err})
        elif path == "/api/add":
            # research-pass.md §2 calls this the highest-leverage sixty seconds in
            # the pipeline: the question the machine would not think to ask.
            beats = {b["id"]: b for b in json.loads(
                (CONVO / "beats.v1.json").read_text(encoding="utf-8"))["beats"]}
            bid = body.get("beat")
            if bid not in beats:
                return self._send(400, {"error": f"unknown beat {bid!r}"})
            if body.get("type") not in ("identify", "enrich", "verify", "contradict", "since"):
                return self._send(400, {"error": "bad type"})
            if not (body.get("question") or "").strip():
                return self._send(400, {"error": "empty question"})

            # Never reuse an id the ledger has already spent. r02 means the Tesla
            # since that was cut; handing it to a new question rewrites history and
            # trips the verifier's ledger-contradiction check.
            led = doc.get("decisions") or {}
            used = {i.get("id") for i in doc.get("queue", [])}
            for e in (led.get("entries") or []) + (led.get("bounced") or []):
                used |= {e.get("was"), e.get("item")}
            nxt = next(f"r{n:02d}" for n in range(1, 100) if f"r{n:02d}" not in used)
            t = body.get("anchor_t")
            t = beats[bid]["t"] if t in (None, "") else float(t)
            item = {
                "id": nxt, "beat": bid, "type": body["type"],
                "anchor_t": t, "anchor_label": f"{int(t // 60):02d}:{int(t % 60):02d}",
                "question": body["question"].strip(),
                "why": (body.get("why") or "Added by hand at Gate 1.").strip(),
                "expected": (body.get("expected") or "").strip() or "Not predicted.",
                "guards": (body.get("guards") or "").strip(),
                "feeds": body.get("feeds") or "check+tendril",
                "human": {"decision": "approved", "by": args.user,
                          "at": date.today().isoformat(), "added_at_gate": True},
            }
            if not (beats[bid]["t"] - 0.001 <= t <= beats[bid]["t_end"] + 0.001):
                item["anchor_outside_window"] = True
                item["anchor_reason"] = "Anchored by hand at Gate 1 outside the beat's clip."
            doc.setdefault("queue", []).append(item)

        elif path == "/api/gate":
            decision = body.get("decision")
            if decision not in ("approved", "changes_requested"):
                return self._send(400, {"error": "bad gate decision"})
            pending = [i for i in doc.get("queue", [])
                       if (i.get("human") or {}).get("decision", "pending") == "pending"]
            if decision == "approved" and pending:
                return self._send(400, {
                    "error": f"{len(pending)} question(s) still pending: "
                             + ", ".join(i["id"] for i in pending)})
            # Never hand 4b a queue the stage itself rejects. Approving past a
            # red verifier is how a bad anchor reaches a paid research job.
            if decision == "approved" and verify()["exit"] != 0:
                return self._send(400, {
                    "error": "verifier is failing — fix the HIGH findings before approving"})
            doc.setdefault("provenance", {})["human_gate"] = {
                "decision": decision, "by": args.user,
                "note": body.get("note") or None, "at": date.today().isoformat(),
            }
        else:
            return self._send(404, {"error": "not found"})

        save(doc)
        self._send(200, state())

    def log_message(self, fmt, *a):
        pass  # the UI is the log


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", args.port), Handler)
    print(f"gate review for {CONVO.name}")
    print(f"editing {QUEUE.relative_to(ROOT) if QUEUE.is_relative_to(ROOT) else QUEUE}")
    print(f"\n  http://127.0.0.1:{args.port}\n")
    print("ctrl-c to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
