# 03: Migrate comment posting to htmx + Alpine

**What to build:** `postComment.html`'s submit flow is rewritten to use htmx and Alpine-driven UI state instead of the current manual `fetch()` + imperative `showError`/`hideError` JS.

**Scope change from the original spec:** the success/review-schedule messaging originally planned for this ticket is dropped. It was written when comments defaulted to `approved: false` (a real pending-review state); since then the site owner switched to auto-approve (`approved: true` by default, see `.scratch/asides/auto-approve-comments.md`), so "submitted for review" would now be actively misleading - comments go live immediately once captcha passes, there's no queue to describe. The site owner explicitly chose not to add any replacement success message either, for now.

**Blocked by:** 01 (independent of ticket 02 - different file, can run in parallel)

**Status:** done

- [x] The form submit is an `hx-post` with `hx-ext="json-enc"`, building the mutation body and headers dynamically
- [x] Because AppSync returns HTTP 200 even when a resolver rejects the request, a small `htmx:afterRequest` listener inspects the parsed response body for a top-level `errors` array and drives Alpine state accordingly
- [x] Alpine (`x-data`/`x-show`) drives all message visibility, replacing the Issue 2 `showError`/`hideError` JS functions
- [x] Existing captcha error behavior from Issue 2 is preserved - verified live: submitting without solving the widget correctly shows "Please complete the captcha before posting." and no network request fires (confirmed by the site owner)
- [x] A successful submission resets the form and the Turnstile widget, and dispatches `refreshComments` on `document.body`
- [x] Verified in a real browser against the live backend: submitting a valid comment (solved widget) succeeded - confirmed via table scan the comment landed `approved: true` (auto-approve), and confirmed by the site owner it appeared in the visible comment list immediately, no manual page reload needed
- [x] No AWS/resolver changes - this ticket is client-side only
- [x] `public/` rebuilt and pushed in the same commit (needed to test the real Turnstile solve, which can't be simulated without a live browser + real domain)

**Post-ship code review refactor:** the inline `js:` attribute expressions in `hx-vals`/`hx-headers` were extracted into named helper functions (`getTurnstileToken`, `resetTurnstile`, `buildCommentHeaders`, `buildCommentVals`), using object-spread (`js:{...buildCommentVals()}`) so htmx's `js:` evaluator still works. Value-preserving by inspection, but given this component's history of subtle bugs that only showed up live (the `selfRequestsOnly` saga), it was re-verified live rather than trusted from static review alone - the site owner confirmed posting still works identically after this refactor shipped.
