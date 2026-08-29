# 01: Scaffold new section structure

**What to build:** Create the four new top-level content sections as empty, buildable Hugo sections, so the migration tickets (02–05) can each move content into an already-existing section independently. This is a prefactor: no existing content moves in this ticket.

**Blocked by:** None (can start immediately)

**Status:** done (commit af305c1)

- [ ] `content/dogs/_index.md` exists with a `title` (and `date` if Hugo's section listing needs one), following the front-matter pattern of the existing `content/BH/_index.md`
- [ ] `content/meetups/_index.md` exists with a `title`
- [ ] `content/tech/_index.md` exists with a `title`
- [ ] `content/misc/_index.md` exists with a `title`
- [ ] None of the four new `_index.md` files contain moved content yet — they are section placeholders only
- [ ] `hugo` builds cleanly with these four new empty sections present alongside the untouched old folders (`BH/`, `IGP/`, `Obedience/`, `Nosework/`, `Protection/`, `Schedule/`, `Misc/`)
- [ ] `public/` is not modified
