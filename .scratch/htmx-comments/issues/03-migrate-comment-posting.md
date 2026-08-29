# 03: Migrate comment posting to htmx + Alpine

**What to build:** `postComment.html`'s submit flow is rewritten to use htmx and Alpine-driven UI state instead of the current manual `fetch()` + imperative `showError`/`hideError` JS.

**Scope change from the original spec:** the success/review-schedule messaging originally planned for this ticket is dropped. It was written when comments defaulted to `approved: false` (a real pending-review state); since then the site owner switched to auto-approve (`approved: true` by default, see `.scratch/asides/auto-approve-comments.md`), so "submitted for review" would now be actively misleading - comments go live immediately once captcha passes, there's no queue to describe. The site owner explicitly chose not to add any replacement success message either, for now.

**Blocked by:** 01 (independent of ticket 02 - different file, can run in parallel)

**Status:** ready-for-agent

- [ ] The form submit is an `hx-post` with `hx-ext="json-enc"`, building the mutation body and headers dynamically (still requires JS for the generated UUID, timestamp, and the Turnstile token from `turnstile.getResponse()` - this is inherent to the feature, not vanilla-JS debt to eliminate)
- [ ] Because AppSync returns HTTP 200 even when a resolver rejects the request, a small `htmx:afterRequest` listener inspects the parsed response body for a top-level `errors` array and drives Alpine state accordingly - htmx's default HTTP-status-based success/failure distinction is not relied on alone
- [ ] Alpine (`x-data`/`x-show`) drives all message visibility, replacing the Issue 2 `showError`/`hideError` JS functions
- [ ] Existing captcha error behavior from Issue 2 is preserved: a distinct message when the widget hasn't been solved, a distinct message when the server rejects the token, and the widget resets after either so the visitor can retry
- [ ] A successful submission still resets the form and the Turnstile widget, and still dispatches `refreshComments` on `document.body` so the comment list (ticket 02) reflects the new comment - matching current (silent) behavior, no new success message
- [ ] Verified in a real browser against the live backend: submitting a valid comment (solved widget) succeeds and lands `approved: true` (per the auto-approve aside) and shows up after the list refreshes; submitting without solving the widget, and a submission that fails server-side verification, both still show their respective distinct error messages with the widget reset for retry
- [ ] No AWS/resolver changes - this ticket is client-side only
- [ ] No changes to `public/` until the final ticket rebuilds it
