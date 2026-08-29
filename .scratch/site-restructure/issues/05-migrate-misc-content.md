# 05: Migrate misc content

**What to build:** `content/Misc/` is renamed to lowercase `content/misc/`, keeping the posts that aren't tech content.

**Blocked by:** 01 (needs `content/misc/_index.md` to already exist)

**Status:** done (commit 446c8b9)

- [ ] `chill.md`, `diet.md`, `small_challegnes.md` are moved from `content/Misc/` into `content/misc/`, front matter and body unchanged
- [ ] `k3s-setup.md` is NOT included here (it belongs to ticket 04 / `content/tech/`) — if ticket 04 hasn't run yet, don't move it either; if it has, don't duplicate it
- [ ] `content/Misc/` (old capitalized folder) is left in place but empty of these three files (final deletion happens in ticket 06) — OR deleted now once confirmed empty; note which approach was taken
- [ ] `hugo` builds cleanly; `/misc/` lists the three migrated posts
- [ ] `public/` is not modified
