# 03: Migrate comment posting to htmx + Alpine, add post-submit messaging

**What to build:** `postComment.html`'s submit flow is rewritten to use htmx and Alpine-driven UI state instead of the current manual `fetch()` + imperative `showError`/`hideError` JS. On a successful submission, two new messages appear: a success confirmation, and a separate note about the comment review schedule/contact - both previously deferred, shipped now since this ticket touches the same code path anyway.

**Blocked by:** 01 (independent of ticket 02 - different file, can run in parallel)

**Status:** ready-for-agent

- [ ] The form submit is an `hx-post` with `hx-ext="json-enc"`, building the mutation body and headers dynamically (still requires JS for the generated UUID, timestamp, and the Turnstile token from `turnstile.getResponse()` - this is inherent to the feature, not vanilla-JS debt to eliminate)
- [ ] Because AppSync returns HTTP 200 even when a resolver rejects the request, a small `htmx:afterRequest` listener inspects the parsed response body for a top-level `errors` array and drives Alpine state accordingly - htmx's default HTTP-status-based success/failure distinction is not relied on alone
- [ ] Alpine (`x-data`/`x-show`) drives all message visibility, replacing the Issue 2 `showError`/`hideError` JS functions
- [ ] Existing captcha error behavior from Issue 2 is preserved: a distinct message when the widget hasn't been solved, a distinct message when the server rejects the token, and the widget resets after either so the visitor can retry
- [ ] On successful submission, two new messages appear together: a success confirmation ("Comment successfully submitted for review" or similar wording) and a separate note about the review schedule/contact ("I review comments on Fridays, or you can email/text me" or similar wording)
- [ ] The review-schedule/contact note contains no actual email address or phone number
- [ ] Verified in a real browser via local `hugo server` against the live backend: submitting a valid comment (solved widget) succeeds, lands `approved: false` (checked via a table read), and shows both new messages; submitting without solving the widget, and a submission that fails server-side verification, both still show their respective distinct error messages with the widget reset for retry
- [ ] No AWS/resolver changes - this ticket is client-side only
- [ ] No changes to `public/` until the final ticket rebuilds it
