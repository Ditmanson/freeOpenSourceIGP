# 03: Migrate meetups content

**What to build:** `content/Schedule/` becomes `content/meetups/`, with all posts carried over unchanged (no new tagging scheme required for this section).

**Blocked by:** 01 (needs `content/meetups/_index.md` to already exist)

**Status:** done (commit 6438e5a)

- [ ] All files from `content/Schedule/` (`13-15march.md`, `29-march-26.md`, `5-april-26.md`, `march_7-8.md`) are moved into `content/meetups/`, preserving filenames and front matter as-is
- [ ] `content/Schedule/` is left in place but empty (final deletion happens in ticket 06) — OR deleted now as long as ticket 06's cleanup accounts for it; note which approach was taken
- [ ] `hugo` builds cleanly; `/meetups/` lists all four migrated posts
- [ ] `public/` is not modified
