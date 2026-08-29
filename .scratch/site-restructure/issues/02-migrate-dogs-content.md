# 02: Migrate dogs content

**What to build:** All dog-sport training posts currently spread across `content/BH/`, `content/IGP/`, `content/Obedience/`, `content/Nosework/`, and `content/Protection/` move into one flat `content/dogs/` section, each tagged with its discipline so the old folder distinction is preserved via `/tags/` instead of via URL structure.

**Blocked by:** 01 (needs `content/dogs/_index.md` to already exist)

**Status:** done (commit 917dca2)

- [ ] Every post file from `content/BH/`, `content/IGP/`, `content/Obedience/`, `content/Nosework/`, `content/Protection/` (excluding `BH/_index.md`, handled separately) is moved into `content/dogs/`, preserving filenames
- [ ] If two source files would collide on filename in the flat `content/dogs/` folder, the collision is flagged rather than one file silently overwriting the other
- [ ] Each migrated post gets exactly one discipline tag added to its `tags:` front matter based on its source folder: `bh`, `igp`, `obedience`, `nosework`, or `protection`
- [ ] Posts that had no `tags:` field before now have one, containing just the discipline tag
- [ ] Posts that had existing tags (e.g. `Griz`, `Argos`, `Tracking`, `Barking`, `Shaping`, `Chill`, `petdogskills` on the relevant files) keep all of them — the discipline tag is additive, not a replacement
- [ ] The heel-map image reference (`/bh_heel_map.png`) currently in `content/BH/_index.md` is preserved somewhere in `content/dogs/` (either in `dogs/_index.md` or in the BH post it's most relevant to) — not silently dropped
- [ ] `content/BH/`, `content/IGP/`, `content/Obedience/`, `content/Nosework/`, `content/Protection/` are left in place but empty of the migrated files (final deletion happens in ticket 06) — OR, if simpler, deleted now as long as ticket 06's cleanup step accounts for it; agent's judgment, note which approach was taken
- [ ] `hugo` builds cleanly; `/dogs/` lists all migrated posts
- [ ] `/tags/bh/`, `/tags/igp/`, `/tags/obedience/`, `/tags/nosework/`, `/tags/protection/` each list the expected posts
- [ ] `public/` is not modified
