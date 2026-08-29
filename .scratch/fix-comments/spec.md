Status: done (completed in commits 3a0a819..e25ba52, tagged v1.1.0)

# Fix the broken commenting section

## Problem Statement

The commenting section on griz.sh (backed by an AWS AppSync GraphQL API over a DynamoDB table, wired up from `layouts/_partials/comments.html` and `layouts/_partials/postComment.html`) is broken — comments can't be loaded or posted. CloudWatch alarms (4xx, 5xx, latency on the AppSync API, wired to an SNS topic) have been firing. Investigation found the root causes:

1. The AppSync API key hardcoded in both partials expired on 2026-07-04 (the site owner discovered this on 2026-08-29) — comments have been unable to authenticate against the API for nearly two months.
2. The `createGrizcomments` resolver is a blind passthrough (`item: ctx.args.input`) with no server-side control over the `approved` field. The client-side `postComment.html` hardcodes `approved: true` on every submission, so — separately from the auth outage — any comment ever successfully posted was immediately live with zero moderation. Given the API key is necessarily public (client-side JS calling a public GraphQL endpoint), this meant anyone who found the key could post instantly-visible comments directly, bypassing the site's form entirely.
3. The DynamoDB table (`grizcomments`) currently holds 2 items, both keyed to page URLs (`postSlug`) from before the site's dogs/meetups/tech/misc restructure — they no longer correspond to any live page and are orphaned.

## Solution

Rotate the expired API key and update both partials with the new one. Change the `createGrizcomments` resolver so it always forces `approved: false` on write, ignoring whatever value the client sends — new comments require manual approval before they're publicly visible again. Clear the two stale table items. Document the manual command the site owner runs to approve a pending comment. Verify the fix against the live AppSync API directly, then against the deployed site once pushed.

## User Stories

1. As a site visitor, I want to see previously-approved comments on a post, so that I can read the discussion.
2. As a site visitor, I want to submit a new comment through the form, so that I can participate in the discussion.
3. As the site owner, I want newly-submitted comments to NOT be publicly visible until I've approved them, so that a stranger or bot posting directly against the public API can't get instant, unmoderated visibility on my site.
4. As the site owner, I want a documented command I can run to approve a specific pending comment, so that legitimate comments eventually become visible without needing new tooling.
5. As the site owner, I want the AppSync API key used by the site to be valid (not expired), so that the comment feature actually works.
6. As the site owner, I want the stale pre-restructure comment rows cleared from the table, so that old data isn't sitting around referencing dead URLs.
7. As the site owner, I want to be able to verify the fix works before pushing to production, so that I don't redeploy a broken comment section again.
8. As the site owner, I want to be told exactly which AWS CLI commands are about to run and confirm before any of them execute, so that I stay in control of changes to my AWS account.

## Implementation Decisions

- **API key rotation**: create a new AppSync API key on the `griz.sh comments` GraphQL API (`3dlgu4u7cjg2pmp5zylj3zvcim`, region `us-east-2`), replacing the expired one in both `comments.html` and `postComment.html`. The old expired key can be left to auto-delete per AppSync's normal key lifecycle (no separate deletion step needed) or explicitly deleted — agent's judgment, whichever is simpler to execute safely.
- **Resolver change**: modify the `createGrizcomments` mutation resolver (AppSync JS runtime) so the item written to DynamoDB always has `approved: false`, regardless of what the client sends in `ctx.args.input.approved`. All other fields (`id`, `name`, `comment`, `postSlug`, `url`, `createdAt`) continue to pass through from client input as today — no schema change, no new required fields.
- **Client-side unchanged in shape**: `postComment.html` keeps sending `approved: true` (or could stop sending it at all) — it no longer matters, since the resolver overrides it either way. Whichever requires the smaller diff is fine; the important thing is the resolver enforces it server-side, not the client.
- **Table cleanup**: delete the 2 existing items in the `grizcomments` DynamoDB table (both orphaned against pre-restructure URLs). No migration of their `postSlug` to new URLs — they're being cleared, not preserved.
- **Approval workflow**: no new tooling. Document the exact `aws dynamodb update-item` (or equivalent AppSync `updateGrizcomments` mutation) command, parameterized by `postSlug` and `createdAt` (the table's composite key), that flips a pending comment's `approved` to `true`. This gets written down (e.g. in the ticket or a short note in the repo) for the site owner to reuse.
- **AWS CLI execution**: the site owner has AWS CLI configured and wants every mutating AWS command (creating the new API key, updating the resolver, deleting the stale items) explicitly surfaced and confirmed before it runs — not bundled into an opaque script. Read-only inspection commands don't need per-command confirmation, but anything that creates/updates/deletes AWS state does.
- **No architecture change beyond this**: the public API key + open write access to the mutation is a known, accepted tradeoff for now (a JAMstack site with a public GraphQL write endpoint has no fully private alternative without a server in front of it). The `approved: false` default is the mitigation for this issue. Further anti-bot hardening (captcha) is explicitly a separate issue (Issue 2) and out of scope here.

## Testing Decisions

- There is no local dev harness for the AppSync API / DynamoDB — this is a live AWS-backed integration, not something unit-testable in isolation, and the repo has no existing test suite to extend.
- The verification seam is **direct GraphQL requests against the live AppSync endpoint** (via `curl` or `aws appsync` tooling) to confirm, independent of the deployed site: querying `listGrizcomments` returns no stale items after cleanup; mutating `createGrizcomments` with `approved: true` in the input still results in a stored item with `approved: false`; the new API key authenticates successfully where the old one would now fail.
- After that direct verification passes, the change is pushed and confirmed against the live deployed site (per the site owner's existing workflow — AWS/Amplify rebuilds on push, and the owner checks the live site directly) as the final, end-to-end check before tagging a release.
- No automated test file is expected to be added — this is an infra/config + small resolver-code fix, not application logic with a test suite precedent in this repo.

## Out of Scope

- Captcha or any other bot-mitigation beyond the `approved: false` moderation gate (that's Issue 2).
- Migrating htmx or changing how the client makes API calls (that's Issue 3).
- Building an approval UI or script — manual CLI/console approval only, per the site owner's explicit choice.
- Preserving or migrating the 2 existing stale comments to their new post URLs.
- Any change to the CloudWatch alarms/SNS topic configuration themselves (only their root causes are being addressed).
- Disabling AppSync schema introspection or other auth-model changes beyond the resolver fix (noted as a possible future hardening, not part of this fix).

## Further Notes

- CloudWatch alarm history shows the `latency alarm` (AppSync `Latency` metric, threshold 3s) has been flapping between `ALARM` and `INSUFFICIENT_DATA` every ~1-2 days over the past week; the `4xx alarm grizsh` and `5xx error grizsh` alarms haven't crossed their threshold (50 errors/5min) in that same recent window, though they plausibly did during the ~2-month expired-key outage before it. Whether these alarms fully settle down after this fix is worth observing once traffic resumes, but is not itself a blocking acceptance criterion — the fix is judged on the direct-API and live-site verification above.
- The AppSync data source description text references AWS account `123456789012` for the DynamoDB table ARN, which doesn't match the actual account (`861079997941`, confirmed via `describe-table`) — this looks like leftover placeholder text from console/tutorial setup, not a real misconfiguration, and doesn't need fixing as part of this issue.
