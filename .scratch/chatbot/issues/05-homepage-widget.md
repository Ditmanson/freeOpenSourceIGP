# 05: Homepage widget

**What to build:** A real visitor can actually use the chatbot on the homepage - a htmx+Alpine chat widget, consistent with the comments feature's UI approach, calling the Lambda Function URL directly from the browser.

**Blocked by:** 03 (wants the Lambda actually answering meaningfully, grounded in real content, before building UI around it)

**Status:** done

- [x] A chat widget (question input, submit, answer display, loading/error/rate-limited states) is added to `layouts/home.html` only - no other template renders it: `layouts/_partials/chatWidget.html` is a new partial, included once from `layouts/home.html`
- [x] `layouts/_partials/head.html`'s existing `{{ if eq .Kind "page" }}` guard is extended to `{{ if or (eq .Kind "page") (eq .Kind "home") }}`, so htmx/Alpine/Mustache load on the homepage too
- [x] The widget calls the Lambda Function URL directly via htmx (`hx-post` to the Function URL, `hx-ext="json-enc"`, `hx-swap="none"`), with Alpine driving all UI state via `htmx:before-request`/`htmx:after-request` listeners - same pattern as `postComment.html`'s `commentForm`
- [x] A rate-limited (429) response shows the backend's own clear message ("You've asked a lot of questions recently...") rather than a generic/broken error - verified live, see below
- [x] Verified in a real browser (Playwright/Chromium, not just curl or a dry read) against the live Lambda: a real question on the homepage produced a real HTTP 200 with a grounded, cited answer rendered in the DOM; visiting a non-homepage page (`/dogs/`) confirmed the widget markup is completely absent
- [x] No AWS/Lambda changes - purely `layouts/` changes
- [x] No changes to `public/`

**Design notes:**

**Local dev-server testing needed one deliberate workaround, documented here so it isn't mistaken for a real bug later:** the Lambda's Function URL CORS policy (set in ticket 01) only allows the `https://griz.sh` origin, by design - so a plain `http://localhost:1313` dev server gets a correct, expected CORS rejection when calling it directly. To get a genuine end-to-end browser test (real network call, real Lambda response, real Alpine/htmx DOM update) rather than stopping at "the request didn't happen," verification used a throwaway Chromium instance launched with `--disable-web-security` (CORS enforcement disabled only in that test browser, no server-side config touched). That confirmed: a normal question renders a real grounded answer, and firing enough requests to cross `MAX_REQUESTS_PER_IP_PER_HOUR` renders the correct rate-limited message text pulled straight from the Lambda's own response body.

**Test-script bug caught and fixed during verification, not a widget bug:** the first rate-limit test's `wait_for_function` checked the answer paragraph's `innerText.length > 0` without checking visibility, so leftover (but now `x-show`-hidden) text from an earlier successful answer satisfied the wait condition immediately on every later iteration - the test looked like it "couldn't reproduce the rate-limited state" when actually the test itself never waited long enough to observe it. Fixed by checking `offsetParent !== null` (visibility) consistently for both the answer and error branches, then re-ran to get a real, confirmed rate-limited screenshot.

**Code review caught two real issues, fixed before shipping:**
1. A `rateLimited` Alpine flag was set on 429 but never actually read anywhere - rate-limited and generic errors rendered through the identical paragraph with no visual distinction beyond message text. Fixed by binding the error paragraph's class to `rateLimited ? 'has-text-warning' : 'has-text-danger'`, giving the rate-limited case genuinely distinct styling, verified live (Chromium, real 429 response) to render `has-text-warning`.
2. `loading` was only ever reset to `false` inside the `htmx:after-request` handler - but a genuine network-level failure (connection refused, an actual CORS rejection, a timeout) fires `htmx:sendError`/`htmx:timeout` instead, which nothing listened for. That would permanently disable the Ask button with no visible error until a page reload. Fixed by adding `handleSendFailure`, wired to both `htmx:send-error.window` and `htmx:timeout.window`, which resets `loading` and shows a clear connectivity error. Verified live by pointing an unmodified (CORS-enforcing) Chromium instance at the local dev server - the real cross-origin rejection now correctly re-enables the button and shows "Couldn't reach the chatbot..." instead of hanging.
