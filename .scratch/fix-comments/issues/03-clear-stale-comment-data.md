# 03: Clear stale comment data

**What to build:** The `grizcomments` DynamoDB table currently holds 2 items keyed to page URLs (`postSlug`) from before the site's dogs/meetups/tech/misc restructure. They no longer correspond to any live page and are deleted.

**Blocked by:** None (can run in parallel with 01/02 — this is a direct DynamoDB operation, not routed through AppSync or the API key)

**Status:** done

- [x] Both existing items in the `grizcomments` table are identified (their `postSlug`/`createdAt` composite keys) and confirmed to reference pre-restructure URLs before deleting anything — both keyed to `postSlug: /obedience/8-month-check-in-griz/` (`createdAt: 2026-06-27T18:21:01.443Z` and `2026-06-27T18:21:22.883Z`), a URL that no longer exists after the site restructure (post now lives at `/dogs/8-month-check-in-griz/`)
- [x] Deleting them is surfaced to the site owner for confirmation before it runs (it's a mutating AWS call) — confirmed via chat before running `aws dynamodb delete-item`
- [x] Both items are deleted from the table
- [x] A follow-up scan/count on the table shows 0 items
- [x] No changes made to `public/` or any repo files — this ticket is AWS-state-only
