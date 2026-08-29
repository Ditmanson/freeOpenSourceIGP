# 02: Wire in real Turnstile keys and build the client widget

**What to build:** The dummy test keys from ticket 01 are replaced with the site owner's real Cloudflare Turnstile key pair, and the comment form (`postComment.html`) gets an actual visible Turnstile widget: script, rendered widget element, and the logic to capture the solved token and send it via the same custom HTTP header the pipeline resolver already reads.

**Blocked by:** 01 (needs the pipeline mechanics proven correct before swapping in real keys and building UI around them)

**Status:** done

- [x] The Turnstile verify function's embedded secret key is swapped from the dummy test secret to the site owner's real secret key — confirmed via chat before applying. Verified live: a `curl` mutation with a garbage token against the real secret is correctly rejected (dummy always-pass key would have accepted it), confirming real Cloudflare validation is active, not just a pass-through.
- [x] `postComment.html` includes the Turnstile widget script and a rendered widget using the site owner's real public site key (`0x4AAAAAAEhVn_r1wv8HHNku`)
- [x] On successful widget solve, the resulting token is captured (via `turnstile.getResponse()`) and sent as the `x-turnstile-token` HTTP header (no schema/API contract change from ticket 01)
- [x] Submitting the form without having solved the widget shows a visible error ("Please complete the captcha before posting."); a captcha rejection from the server shows a distinct error ("Captcha verification failed. Please try again.") and resets the widget via `turnstile.reset()` so the visitor can retry
- [x] `listGrizcomments`/comment display behavior is unchanged — nothing in `comments.html` was touched
- [x] Widget rendering and solving verified via a real browser against a local `hugo server` (required adding `localhost` to the Turnstile widget's allowed domains in the Cloudflare dashboard, since Turnstile validates the requesting hostname) — widget correctly auto-solved in Managed mode (green success indicator with no click needed, which is expected Turnstile behavior, not a bug)

**Code review fixes applied:** the initial captcha-error check used `errorType === "Unauthorized"`, which is too broad — AppSync also returns `Unauthorized` for e.g. an invalid API key (exactly the failure mode from Issue 1), which would have shown a misleading "Captcha verification failed" message for an unrelated auth problem. Now matches on the resolver's actual error message text ("Turnstile...") instead. Also consolidated the repeated `turnstile.reset()` guard into a helper and switched inline `color: red` to Bulma's `has-text-danger` class, matching the rest of the site's styling.

**Deferred to ticket 03, by the site owner's choice:** the actual form-submission round trip (solve widget → submit → comment lands `approved:false`) was not exercised against localhost — the site owner chose to skip local end-to-end testing and verify the full chain directly on the live site instead, which ticket 03 already covers. Everything gate-able independently (resolver correctness with real keys, widget rendering/solving, error UX) is confirmed; only the final full-chain proof moves to ticket 03.
