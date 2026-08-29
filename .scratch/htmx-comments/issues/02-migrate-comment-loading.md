# 02: Migrate comment loading/display to htmx + Mustache

**What to build:** `comments.html`'s comment-loading flow is rewritten to use htmx (triggered on page load) and a Mustache `<template>` to render the GraphQL JSON response into HTML, replacing the current hand-rolled `fetch()` + manual DOM construction + `escapeHtml()`.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] The comment-loading request is an `hx-post` (GraphQL is POST-only) triggered on load, using `hx-ext="json-enc,client-side-templates"` and a named Mustache `<template>` to render the response
- [ ] The Mustache template uses a loop section for the comment list and an inverted (empty-case) section for "no comments yet" - matching current behavior, replacing the manual `commentsList`/`noCommentsMessage` show/hide JS
- [ ] Comment `name`/`comment` text is rendered via Mustache's default auto-escaping (`{{variable}}`, not `{{{triple-stash}}}`) - the hand-rolled `escapeHtml()` function is removed, not kept alongside
- [ ] The `postSlug` filter (currently `window.location.pathname`) and `approved: true` filter are still correctly applied to the request
- [ ] Verified in a real browser via local `hugo server` against the live backend: a post with existing approved comments renders them correctly; a post with zero comments shows the empty state correctly
- [ ] No AWS/resolver changes - this ticket is client-side only
- [ ] No changes to `public/` until the final ticket rebuilds it
