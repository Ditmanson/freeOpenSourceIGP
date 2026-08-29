# 01: Add htmx/Mustache/Alpine dependencies

**What to build:** The shared script dependencies needed for both migration tickets are added once, in one place, so tickets 02 and 03 can each just build against them rather than each needing to add and coordinate script loading themselves.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] Pinned-version CDN `<script>` tags for htmx (2.0.10), the `htmx-ext-client-side-templates` extension (2.0.2), Mustache.js (4.2.0), and Alpine.js (3.16.3) are added to `layouts/_partials/head.html` — versions confirmed as latest-stable via the npm registry, and each exact CDN URL confirmed to resolve (HTTP 200) before use
- [x] No pinned version uses `@latest` or an unpinned tag
- [x] Alpine.js is loaded with `defer`
- [x] `hugo` builds cleanly; the scripts are present in rendered page output (verified via a real build, not just source inspection)
- [x] In a real browser (local `hugo server`), devtools console confirms `htmx`, `Alpine`, and `Mustache` are all defined globals, with no console errors — confirmed by the site owner
- [x] No visible behavior change yet - `comments.html` and `postComment.html` are untouched by this ticket
- [x] No changes to `public/` - confirmed clean throughout (used `hugo server --renderToMemory` for local testing this time, avoiding the disk-write flakiness seen in earlier tickets)

**Code review fixes applied:** the scripts were originally loading unconditionally on all 77 pages via the shared `head.html`, but only `layouts/page.html` (individual post pages) actually renders `comments.html`/`postComment.html` - section/home/tag pages never use them. Wrapped the script tags in `{{ if eq .Kind "page" }}` so they only load where needed. Also fixed an inconsistent loading strategy (3 blocking scripts + 1 deferred) by making all four scripts consistently `defer`. Re-verified in a real browser after both fixes: a post page still has all three globals defined, the homepage correctly has none of them, matching the guard's intent.
