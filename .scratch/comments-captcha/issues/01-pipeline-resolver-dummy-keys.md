# 01: Build and verify the pipeline resolver mechanics (dummy test keys)

**What to build:** `Mutation.createGrizcomments` becomes a two-step AppSync pipeline resolver — verify a Turnstile token against Cloudflare first, only write to DynamoDB if verification succeeds. Proven server-side using Cloudflare's fixed dummy test key pairs (one that always passes verification, one that always fails), so the pass/fail branches are confirmed correct before any real keys or client UI exist.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] A new AppSync HTTP data source exists, pointed at Cloudflare's Turnstile verify endpoint — `turnstileVerify`, `https://challenges.cloudflare.com`
- [x] `Mutation.createGrizcomments` is converted from a UNIT resolver to a PIPELINE resolver with two functions in order: (1) `verifyTurnstile` calling the HTTP data source, (2) `writeCommentToDynamo` containing the existing DynamoDB `put` logic (still forcing `approved: false`, unchanged from Issue 1)
- [x] The verify function reads the Turnstile token from a custom HTTP header (`x-turnstile-token`) on the incoming request, not from a new GraphQL input field — no schema change
- [x] If verification fails (or the token header is missing/malformed), the pipeline stops before the write function runs — no DynamoDB call happens at all
- [x] Every mutating AWS command (data source, both functions, resolver update, plus the temporary fail-key swap for testing) was surfaced to the site owner for confirmation before running
- [x] Direct `curl` test: a `createGrizcomments` call with any token, verified against Cloudflare's dummy always-pass secret, succeeds and the item lands in DynamoDB with `approved: false` — tested and cleaned up (`/__ticket01-pipeline-test__`)
- [x] Direct `curl` test: `createGrizcomments` calls verified against Cloudflare's dummy always-fail secret (both with and without a token header) are rejected with `Unauthorized`/"Turnstile verification failed", and a follow-up `get-item` confirmed nothing was written to DynamoDB
- [x] `listGrizcomments`, `getGrizcomments`, subscriptions, and `updateGrizcomments` are all untouched by this ticket — verified `listGrizcomments` still returns data normally and `updateGrizcomments` is still the `UNIT` reject-everything resolver from the earlier aside fix
- [x] No changes to `public/` or any client-facing files — this ticket is AppSync/resolver-only

**Note:** the verify function's secret was temporarily swapped to the dummy always-fail key to prove the reject path, then swapped back to the always-pass dummy key (the resting state for this ticket) — both swaps were confirmed with the site owner first.

**Note for future resolver work:** code review flagged that `JSON.parse(ctx.result.body)` in the verify function was unguarded — if Cloudflare ever returned a non-JSON body (outage, rate-limit page), this would throw. First attempt was a `try`/`catch`, which failed to deploy (`CODE_ERROR`): **AppSync's JS resolver runtime does not support `try`/`catch`** at all — it's a restricted runtime that expects `util.error()` for control flow instead of exceptions. Fixed properly using that idiom instead: the response function now checks `ctx.result.statusCode !== 200` and calls `util.error()` before ever attempting to parse the body, guarding the most likely real failure mode (Cloudflare returning a non-2xx response) without needing exception handling. Re-verified both the pass and fail paths still work correctly with the guard in place. Worth remembering for any future AppSync JS resolver work in this API: no try/catch, use `util.error()` as the control-flow primitive instead.
