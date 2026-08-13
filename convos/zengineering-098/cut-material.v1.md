# E098 — material cut from the published episode

Transcribed from the isolated per-speaker tracks, from the six windows the Audition session
removes between the final mix and the released master. **None of this is in the published
episode.** 99.2 seconds total, of which 12.1 s was promoted to the cold open and 87.1 s was
discarded.

Timestamps are **final-mix / raw-track seconds**, not master seconds. The master timeline does not
address this material at all — see `source.json` → `edit_map`.

> faster-whisper-class model (whisper.cpp `small.en`), one pass per track, speaker by track
> ownership. No diarization involved: attribution here is exact.
> Produced by `skill/stages/stage2b_cut_material.py`.

---

## Cut 2 — mix 1240.6–1297.5 (56.9 s, 20:40) — the one that matters

This is where the cold open was lifted from. The published episode opens with the first four
sentences of it; the rest was cut.

**TBJ** _[20:40]_

Well, you— sorry, go ahead. That's never happened before in 100 episodes. I don't think we've ever
done what we just did. But yeah, seriously, I don't think that's ever happened before. Weird. Did
that not strike you as weird? [laughter]

**Adam** _[20:40]_

Um, the, go ahead. What both tried to yield. I spend all day on calls and now I'm getting better at
it. Uh, anyway, so I don't know. It just happens to me all day now. Cause I'm constantly like, I
have a thing to say, but it's not helpful for the conversation. So I'll let someone else speak.

**TBJ** _[21:10]_

I never have that thought either. [laughter] We might have killed both of them. Oh, I was going to
say, oh, you're touching on another— let me start that over.

**Adam** _[21:10]_

Uh, I was going to say, so, you know, so that, that should exist at the same time. Um, no, I lost
it. What were you going to say? Do you remember? It's okay.

**Where the master resumes:** at master 20:53, TBJ says *"You're touching on another really critical
piece of this…"* — the restart he announces in the last line above. The edit is seamless because he
did the work of making it seamless, out loud, in material that was then cut.

---

## Cut 5 — mix 2628.5–2659.0 (30.5 s, 43:48) — a technical failure

**TBJ** _[43:48]_ Your video dropped. Your audio looks like it's still there. Check, check, check,
check. Yeah.

**Adam** _[43:48]_ Ultimately— oh, I think my audio just dropped. Let me double check that I'm
still— check, check. Yeah, let me double check that I'm on the right input. I can't do that
without— check, check. Is that thumpy for you? OK, I think we're good.

Correctly cut. Recorded here because a `since` question about remote recording in 2020 has evidence
sitting in it.

---

## Cuts 1, 3, 4, 6 — 11.8 s total, no content

| Cut | Mix window | Length | Content |
|---|---|---|---|
| 1 | 247.5–250.6 | 3.0 s | Adam: "You know." |
| 3 | 1533.5–1536.6 | 3.1 s | silence |
| 4 | 1537.1–1538.1 | 1.0 s | silence |
| 6 | 2684.7–2689.4 | 4.7 s | Adam: "Uh, yeah." |

---

## Why this file exists

The beat schema in `convo-v1-spec.md` §2 gives a beat `t` and `t_end` on the master timeline only.
Cut 2 is not addressable by that schema, and it is the strongest `since` claim in the episode. A
beat needs a source-timeline field, or the pipeline can only ever describe the episode as released
— which is exactly the thing show notes already do.
