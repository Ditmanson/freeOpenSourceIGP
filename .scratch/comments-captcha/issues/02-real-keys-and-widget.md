# 02: Wire in real Turnstile keys and build the client widget

**What to build:** The dummy test keys from ticket 01 are replaced with the site owner's real Cloudflare Turnstile key pair, and the comment form (`postComment.html`) gets an actual visible Turnstile widget: script, rendered widget element, and the logic to capture the solved token and send it via the same custom HTTP header the pipeline resolver already reads.

**Blocked by:** 01 (needs the pipeline mechanics proven correct before swapping in real keys and building UI around them)

**Status:** ready-for-agent

- [ ] The Turnstile verify function's embedded secret key is swapped from the dummy test secret to the site owner's real secret key — surfaced for confirmation before applying, same as any other mutating AWS resolver update
- [ ] `postComment.html` includes the Turnstile widget script and a rendered widget using the site owner's real public site key
- [ ] On successful widget solve, the resulting token is captured and sent as the same custom HTTP header the pipeline resolver reads (no schema/API contract change from ticket 01)
- [ ] Submitting the form without having solved the widget (or after the token expires) shows *some* visible error to the visitor — enough to know to retry, not the fuller deferred "submitted for review" messaging
- [ ] A real solved Turnstile challenge, submitted through the form, results in a comment landing in DynamoDB with `approved: false` (same behavior as before captcha existed, just now gated on a real solve)
- [ ] `listGrizcomments`/comment display behavior is unchanged — captcha only gates posting, not reading
- [ ] Verified via a real browser (the site owner solving the actual widget), since this can't be scripted
