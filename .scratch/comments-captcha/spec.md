Status: done (completed in commits 533f7a5..7307e02)

# Add captcha to the comment form

## Problem Statement

The comment form (`layouts/_partials/postComment.html`, backed by the `createGrizcomments` AppSync mutation) has no anti-bot protection. Issue 1 closed the moderation bypass (new comments now default to `approved: false` server-side, so nothing posted directly against the public API can go live unreviewed), but nothing stops a bot from spamming `createGrizcomments` in the first place. Even though spammed comments can't go public, a flood of them pollutes the pending-approval queue (`scripts/list-unapproved-comments.py` / `scripts/approve-comments.py`, built in the interim between Issue 1 and this issue) and costs real (if currently small) AppSync/DynamoDB usage money.

Note: while scoping this issue, a related but separate defacement gap was found and fixed as a standalone aside (not part of this spec): `updateGrizcomments` allowed anyone with the public API key to overwrite any existing comment's text. That mutation now rejects all client calls outright. See `.scratch/asides/disable-update-mutation.md`.

## Solution

Add Cloudflare Turnstile to the comment form, verified **server-side** — a bot that skips the visible widget and calls `createGrizcomments` directly must still pass verification, because the AppSync resolver itself calls Cloudflare's verify endpoint before ever writing to DynamoDB. `createGrizcomments` becomes a two-step AppSync pipeline resolver: first a new HTTP data source function verifies the client-supplied Turnstile token against Cloudflare, then (only on success) the existing DynamoDB write proceeds exactly as it does today (still forcing `approved: false`, per Issue 1 - unchanged).

## User Stories

1. As a site visitor, I want to complete a Turnstile challenge before my comment is accepted, so that the site can tell I'm not an automated bot.
2. As a site visitor whose Turnstile challenge fails or expires, I want to see a clear error so I know to retry, rather than the form silently doing nothing.
3. As the site owner, I want comment submissions that bypass the visible widget and call the GraphQL mutation directly to still be rejected unless they present a valid Turnstile token, so that captcha can't be trivially defeated by skipping the browser UI.
4. As the site owner, I want the Turnstile secret key to live only in server-side AppSync resolver code, never in any client-visible file or the public API surface, so that it can't be extracted and reused to forge verifications.
5. As the site owner, I want the existing moderation behavior (new comments default to `approved: false`) to be completely unchanged by this work, so that captcha and moderation remain two independent, layered defenses.
6. As the site owner, I want to verify the resolver's verify-then-write pipeline logic against Cloudflare's dummy test keys before wiring in my real Turnstile keys, so that I can confirm the pass/fail branches work correctly without needing a browser.
7. As the site owner, I want to do a final real-browser check on the live site (solving the actual widget) before tagging a release, so that the whole chain is proven end-to-end, not just server-side.
8. As a site visitor browsing without commenting, I want page load and comment display (`listGrizcomments`) to be completely unaffected by this change, so that captcha only adds friction at the point of posting, not reading.

## Implementation Decisions

- **Provider**: Cloudflare Turnstile (Managed widget mode). Chosen over AWS WAF CAPTCHA (real ongoing cost, ~$5-7+/month baseline, for a threat that's currently unconfirmed) and over Google reCAPTCHA/hCaptcha (Turnstile is free and more privacy-respecting). Site key and secret key already obtained by the site owner via a guided setup script; site key is public (`0x4AAAAAAEhVn_r1wv8HHNku`), secret key is held privately and will be embedded directly in the new server-side resolver code (same trust model as the existing DynamoDB resolver code - not visible to clients, only to whoever has AWS access).
- **Client-side widget**: the Turnstile widget script and a rendered widget element are added to `postComment.html`, using the public site key. On solve, the widget produces a token.
- **Token transport**: the client sends the Turnstile token as a custom HTTP header on the `createGrizcomments` request (not as a new field on `CreateGrizcommentsInput`). This avoids a GraphQL schema change entirely. AppSync JS resolvers can read incoming HTTP headers via the resolver context, so the new HTTP-verification pipeline function reads the token from there.
- **Pipeline resolver**: `Mutation.createGrizcomments` changes from a UNIT resolver (DynamoDB only) to a PIPELINE resolver with two functions, in order:
  1. **Verify function** (new HTTP data source pointed at Cloudflare's Turnstile verify endpoint): sends the client's token + the embedded secret key; if Cloudflare reports failure (or the header is missing/malformed), the pipeline stops here and returns a GraphQL error - no DynamoDB call happens at all.
  2. **Write function** (existing DynamoDB data source, existing logic unchanged): the current `put` logic that forces `item.approved = false` regardless of client input, exactly as ticket 02 of Issue 1 left it.
- **No schema change**: `CreateGrizcommentsInput`, `UpdateGrizcommentsInput`, and all other types are untouched.
- **No change to `updateGrizcomments`, `listGrizcomments`, `getGrizcomments`, or subscriptions**: captcha only gates the create-comment write path. Reading comments stays exactly as fast/frictionless as today.
- **Error UX**: when the pipeline rejects a submission (missing/invalid/expired token, or Cloudflare verification failure), the client shows *some* visible error to the user - at minimum enough that a legitimate visitor whose challenge expired understands to retry. This is the minimum viable feedback needed for the feature to be usable and debuggable, not the fuller "comment submitted for review" success-state messaging the site owner has explicitly deferred to a later, separate piece of work.
- **AWS CLI execution**: as with Issue 1, every mutating AWS command (creating the HTTP data source, creating/updating pipeline functions, updating the resolver to PIPELINE kind) is surfaced to the site owner for confirmation before it runs. Read-only inspection doesn't need per-command confirmation.

## Testing Decisions

- Same as Issue 1: no local dev harness exists for AppSync/DynamoDB, and this repo has no test suite to extend. Verification happens directly against live AWS resources, then against the deployed site.
- **Server-side pipeline verification without a browser**: Cloudflare publishes fixed dummy site-key/secret-key pairs for exactly this purpose - one pair that always passes verification, one that always fails, regardless of the token value sent. The new pipeline resolver's pass and fail branches are both exercised directly (via `curl`/AppSync test-invoke style calls) using these dummy keys before the real production Turnstile keys are wired in. This proves the resolver logic (verify-then-write, reject-without-writing) independent of ever needing a real solved challenge.
- Once the pipeline logic is confirmed correct with dummy keys, the real site/secret key pair replaces them.
- **Final live check**: after pushing (remembering the Issue-1-discovered gotcha that `public/` must be manually rebuilt with `hugo` and committed separately, since AWS Amplify's build for this app doesn't run `hugo build`), the site owner does one real end-to-end pass in an actual browser: solve the widget, submit a comment, confirm it's accepted (lands `approved: false`, same as before); separately, confirm that a raw `curl` mutation call with no/garbage token is rejected.
- No automated test file is expected - this is an infra/resolver change, not application logic with a test-suite precedent in this repo.

## Out of Scope

- The general "comment submitted for review" success-state UX overhaul (explicitly deferred by the site owner during Issue 1's wrap-up).
- Any change to the moderation/approval logic from Issue 1 - `approved` still always starts `false`, still can't be set by any client mutation.
- Any change to `updateGrizcomments` beyond the standalone aside fix already applied (full rejection of client updates).
- AWS WAF CAPTCHA or any other provider besides Cloudflare Turnstile.
- Rate limiting, IP blocking, or any anti-bot measure beyond the captcha challenge itself.
- Issue 3 (htmx migration for API calls) - not started here.

## Further Notes

- This issue's investigation surfaced the `updateGrizcomments` defacement gap, which was fixed as a standalone aside outside this spec's tickets (see `.scratch/asides/disable-update-mutation.md`) - already committed and verified live before this spec was written.
- The site owner explicitly asked "what happens if I skip captcha entirely" before committing to this work; the honest answer (recorded here for future reference) was: no confirmed bot activity has been observed in the table to date, cost risk is low but non-zero if bots ever do show up, AppSync/DynamoDB won't "go down" from bot load since both are managed/auto-scaling, and the main practical cost of skipping this would be a polluted manual-approval queue. The site owner chose to proceed with Turnstile anyway as preventive hardening.
