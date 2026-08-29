Status: ready-for-agent

# Migrate comments to htmx, add post-submit messaging

## Problem Statement

`layouts/_partials/comments.html` and `layouts/_partials/postComment.html` both hand-roll their GraphQL API calls in vanilla JS: manual `fetch()`, manual `JSON.parse`, manual DOM construction (`createElement`/`innerHTML`), and a hand-written `escapeHtml()` for XSS protection. The site owner wants this rewritten to use htmx instead. A prior attempt (`layouts/_partials/bak/comments_htmx_dontwork.html`) failed because it pointed `hx-get` directly at a JSON REST endpoint with `hx-swap="innerHTML"` - htmx expects HTML back to swap into the page, and dumping raw JSON into a div just displays JSON text, not rendered comments. This repo's backend (AWS AppSync) only ever returns JSON (GraphQL), so a straightforward htmx swap can't work here without a bridge.

Separately, when a comment is successfully submitted, the form currently gives no feedback at all beyond silently resetting - this was flagged as a rough edge during Issue 1's live testing and explicitly deferred to "later." The site owner now wants that feedback added.

## Solution

Add htmx, plus its official `client-side-templates` extension and Mustache.js, to bridge GraphQL's JSON responses into rendered HTML via `<template>` tags - the documented, idiomatic htmx pattern for JSON APIs (not a workaround). Add Alpine.js alongside it for small client-side-only UI state (showing/hiding messages) that doesn't need a server round-trip, replacing the hand-written `showError`/`hideError` JS functions from Issue 2 with declarative `x-show` attributes. On successful submission, show two new message blocks: a success confirmation, and a separate note about the review schedule/contact - both currently deferred and shipped together as part of this same rewrite, since they touch the exact same submit-handling code path being migrated anyway.

This migration will not eliminate all JavaScript. Building the GraphQL mutation's dynamic values (a generated UUID, a timestamp, the Turnstile token capture via Turnstile's own JS API) still requires JS regardless of htmx - htmx and its extensions replace the request-sending and response-rendering boilerplate, not every line of script in these two files.

## User Stories

1. As a site visitor, I want to see existing comments on a post load correctly, the same as today, so that the htmx rewrite is a pure implementation change with no visible regression.
2. As a site visitor, I want to submit a comment through the form and see it work the same as today (subject to the moderation and captcha gates from Issues 1-2), so that this rewrite doesn't change what I'm able to do, only how it's built.
3. As a site visitor who successfully submits a comment, I want to see a clear "Comment successfully submitted for review" message, so that I know my submission was received rather than wondering if anything happened.
4. As a site visitor who successfully submits a comment, I want to see a separate note about when/how comments get reviewed (e.g. "I review comments on Fridays, or you can email/text me"), so that I have a sense of when to expect it to appear, without the site publishing any actual contact details.
5. As the site owner, I want no email address or phone number published in this note, so that only people who already know how to reach me understand the reference.
6. As the site owner, I want the empty-comments state ("No comments yet") to keep working correctly under the new templating approach, so that posts with zero comments still render sensibly.
7. As the site owner, I want comment text to still be safely HTML-escaped when rendered, so that a comment containing HTML/script-like text can't inject anything into the page - handled by Mustache's default auto-escaping rather than the current hand-rolled `escapeHtml()` function.
8. As the site owner, I want the existing captcha error-handling behavior from Issue 2 (distinct messages for "widget not solved" vs "server rejected it," widget reset for retry) preserved under the new Alpine-driven UI, not silently dropped during the rewrite.
9. As the site owner, I want to verify this works locally against the real, already-live backend before pushing, so that I'm not deploying an untested rewrite of a feature that's had two real outages already (Issues 1 and 2).
10. As the site owner, I want a final live-site check before tagging a release, matching the rhythm established in Issues 1 and 2.

## Implementation Decisions

- **New shared dependencies**: htmx, the `htmx-ext-client-side-templates` extension, Mustache.js, and Alpine.js, all loaded via pinned-version CDN `<script>` tags (matching the site's existing pattern for Bulma CSS) - added once in `layouts/_partials/head.html` (shared by every page, since both `comments.html` and `postComment.html` render on every page via `page.html`), not duplicated per-partial like the current ad-hoc Turnstile script placement.
- **`comments.html` (load/display)**: the comment-loading request becomes an `hx-post` (GraphQL is POST-only) triggered on load, using `hx-ext="json-enc,client-side-templates"` to send a JSON body and render the JSON response through a named Mustache `<template>`. The template uses a `{{#items}}...{{/items}}` loop for the comment list and Mustache's inverted-section syntax for the "no comments yet" empty state, replacing the current manual `commentsList`/`noCommentsMessage` show/hide JS. `escapeHtml()` is removed; Mustache's default `{{variable}}` escaping (not `{{{triple-stash}}}`) is relied on for XSS safety instead.
- **`postComment.html` (post)**: the form submit becomes an `hx-post` with `hx-ext="json-enc"`, building the GraphQL mutation body and headers dynamically via htmx's `js:` expression syntax (still needs the generated UUID, timestamp, and the Turnstile token from `turnstile.getResponse()` - this is inherent to the feature, not left-over vanilla-JS debt).
- **GraphQL's "always 200" gotcha**: AppSync returns HTTP 200 even when a resolver rejects the request (e.g. Issue 2's Turnstile failure), so htmx's default success/failure distinction (based on HTTP status) can't be relied on alone. A small `htmx:afterRequest` listener inspects the parsed response body for a top-level `errors` array and sets Alpine state accordingly, rather than assuming a 200 response means success.
- **Alpine-driven UI state**: replaces the Issue 2 `showError`/`hideError` JS functions with `x-data`/`x-show` attributes. Adds two new states shown together after a successful submission: the success confirmation message, and the separate review-schedule/contact note. Existing captcha error messaging (widget-not-solved vs. server-rejected, with widget reset) is preserved, just re-expressed declaratively instead of imperatively.
- **New copy** (exact wording is an implementation-time judgment call within this spirit): a success message along the lines of "Comment successfully submitted for review," and a separate note along the lines of "I review comments on Fridays, or you can email/text me" - deliberately with **no actual email address or phone number** in the markup, since it's meant as a recognizable heads-up only to people who already have the site owner's contact info, not a public contact channel.
- **No AWS/resolver changes**: this issue is entirely client-side (`layouts/_partials/`, `head.html`). Nothing about the AppSync pipeline, DynamoDB, or the moderation/captcha logic from Issues 1-2 changes.

## Testing Decisions

- No local dev harness/test suite exists for this repo, same as Issues 1-2, but unlike those issues, this one makes no AWS-mutating calls at all - it's a pure client-side rewrite hitting the same, already-live, already-working backend.
- Primary verification seam: a local `hugo server` (not `hugo` alone - server mode is needed to interact with the page live) against the real backend, in an actual browser, checking: existing comments still load and render correctly; the empty state still shows correctly on a post with no comments; submitting a comment still works end-to-end including the captcha gate; the two new post-submit messages appear; captcha error states still show and allow retry.
- After local verification, the same rebuild-and-push rhythm from Issues 1-2 applies (remembering `docs/deploys.md`'s Amplify gotcha) before a final live-site check and tagging a release.
- No automated test file is expected - this repo has no test-suite precedent for template/frontend code.

## Out of Scope

- Automating comment review or owner notifications (explicitly deferred by the site owner - "I'll eventually automate this stuff but we don't have infrastructure for that").
- Publishing any actual email address or phone number.
- Any change to the AppSync resolvers, DynamoDB table, or the moderation/captcha behavior from Issues 1-2 - this is a pure client-side rewrite of already-correct backend interactions.
- Removing or changing the Turnstile widget itself (Issue 2's work) - only its error-messaging UI moves to Alpine.
- A build step/bundler for htmx/Alpine/Mustache - CDN script tags only, matching the rest of this site's dependency style.

## Further Notes

- The failed prior attempt (`layouts/_partials/bak/comments_htmx_dontwork.html`) is left in place as historical reference; not deleted or modified by this work.
- This is a good opportunity to also delete the other now-long-stale backup files in `layouts/_partials/bak/` (`comments.html.bak`, `postComment.html.bak`) if they're confirmed to be pre-AppSync-migration artifacts with no remaining reference value - a small cleanup judgment call for whoever picks up the first ticket, not a hard requirement.
