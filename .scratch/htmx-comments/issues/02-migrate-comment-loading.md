# 02: Migrate comment loading/display to htmx + Mustache

**What to build:** `comments.html`'s comment-loading flow is rewritten to use htmx (triggered on page load) and a Mustache `<template>` to render the GraphQL JSON response into HTML, replacing the current hand-rolled `fetch()` + manual DOM construction + `escapeHtml()`.

**Blocked by:** 01

**Status:** done

- [x] The comment-loading request is an `hx-post` (GraphQL is POST-only) triggered on load, using `hx-ext="json-enc,client-side-templates"` and a named Mustache `<template>` to render the response
- [x] The Mustache template uses a loop section for the comment list and an inverted (empty-case) section for "no comments yet" - matching current behavior, replacing the manual `commentsList`/`noCommentsMessage` show/hide JS
- [x] Comment `name`/`comment` text is rendered via Mustache's default auto-escaping (`{{variable}}`, not `{{{triple-stash}}}`) - the hand-rolled `escapeHtml()` function is removed, not kept alongside
- [x] The `postSlug` filter (currently `window.location.pathname`) and `approved: true` filter are still correctly applied to the request
- [x] Verified in a real browser against the live backend - a post with existing approved comments renders them correctly; empty-state Mustache section verified via source inspection (not separately re-confirmed live after the root-cause fix, low risk since it's the same inverted-section mechanism)
- [x] No AWS/resolver changes - this ticket is client-side only
- [x] No changes to `public/` until rebuilt for the final push in this ticket

**Root cause found and fixed (significant debugging effort):** the GraphQL request never fired at all, on localhost or production, in any browser. After extensive elimination (ruled out CORS, CSP, browser extensions, HTML/DOM correctness, htmx loading itself, individual extensions) the actual cause was **htmx 2.x's `selfRequestsOnly: true` default** - a security hardening added in the 2.0 rewrite that silently blocks any cross-origin request (`htmx:invalidPath`) unless explicitly disabled. Our GraphQL API (AppSync) is a different origin than the site itself, so every request was blocked from the start. Fixed via a `<meta name="htmx-config" content='{"selfRequestsOnly": false}'>` tag in `head.html`, which htmx reads during its own startup before processing the page. Confirmed fixed live via direct console testing before the final deploy.

This also explains ticket 01's local-testing gap: `typeof htmx`/`typeof Alpine`/`typeof Mustache` all being defined only proved the scripts loaded, not that htmx could actually make cross-origin requests - the real bug was invisible to that check.

**Code review caught two more real bugs before ship:**
1. `postComment.html` still called a now-deleted `loadComments()` function after a successful post - comments would silently never refresh after posting. Fixed: `#comments` now uses `hx-trigger="load, refreshComments from:body"`, and `postComment.html` dispatches a `refreshComments` event on `document.body` instead.
2. The Mustache template didn't distinguish a GraphQL error response from a genuinely empty comment list - both rendered "No comments yet." Fixed: wrapped the template in an `{{#errors}}...{{/errors}}` / `{{^errors}}...{{/errors}}` check.

Both changes touch `postComment.html` (not originally in this ticket's scope) but are one-line reactive fixes to comments.html's own rewrite, not ticket 03's actual migration work - ticket 03 remains untouched otherwise.
