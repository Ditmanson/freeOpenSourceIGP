# 04: Migrate tech content

**What to build:** `content/Misc/k3s-setup.md` moves out of `Misc` into its own new `content/tech/` section.

**Blocked by:** 01 (needs `content/tech/_index.md` to already exist)

**Status:** done (commit 9b444a5)

- [ ] `content/Misc/k3s-setup.md` is moved to `content/tech/k3s-setup.md`, front matter and body unchanged
- [ ] `content/Misc/` still contains `chill.md`, `diet.md`, `small_challegnes.md` untouched (those move in ticket 05, not this one)
- [ ] `hugo` builds cleanly; `/tech/` lists the k3s post and it renders correctly
- [ ] `public/` is not modified
