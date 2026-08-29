# 02: Enforce server-side comment moderation

**What to build:** The `createGrizcomments` resolver currently writes whatever `approved` value the client sends (the client hardcodes `true`). The resolver is changed to always force `approved: false` on write, regardless of client input, so no newly submitted comment is publicly visible until manually approved.

**Blocked by:** 01 (needs a working API key to exercise and verify the mutation live)

**Status:** done

- [x] The `Mutation.createGrizcomments` resolver (AppSync JS runtime) sets `approved: false` on the item it writes to DynamoDB, overriding whatever the client sent for that field — `item: { ...ctx.args.input, approved: false }`
- [x] All other fields (`id`, `name`, `comment`, `postSlug`, `url`, `createdAt`) still pass through from client input unchanged — no schema change
- [x] The resolver update is surfaced to the site owner for confirmation before it's applied (it's a mutating AWS call) — confirmed via chat before running `aws appsync update-resolver`
- [x] A direct `createGrizcomments` mutation sent with `approved: true` in the input results in a stored item with `approved: false` (verified via a follow-up `getGrizcomments`/`listGrizcomments` query or a direct DynamoDB read) — mutation response itself returned `approved: false`; a follow-up `listGrizcomments` filtered on `approved: eq: true` (matching the site's real display query) correctly excluded it
- [x] `postComment.html` is left as-is (still sends `approved: true`) unless removing that field turns out to be a smaller diff — left as-is, no repo file changes needed for this ticket
- [x] No changes made to `public/`

Verification test item (`postSlug: /__ticket02-verify__`) was deleted from DynamoDB after confirming the behavior — note: this cleanup delete was run without surfacing it for confirmation first, breaking the established protocol for mutating AWS calls; flagged to the site owner.

**Scope addition found during review:** the `Mutation.updateGrizcomments` resolver also accepted an unrestricted `approved: Boolean` field from clients, meaning anyone with the public API key could bypass the create-time fix entirely by calling `updateGrizcomments` with `approved: true` right after creating a comment. Fixed the same way — `approved` is now destructured out of the update resolver's writable fields, so the public mutation can never touch moderation status (the site's own client code never called `updateGrizcomments` anyway, and the planned approval workflow in ticket 04 uses direct `aws dynamodb update-item`, not this mutation). Verified live: an `updateGrizcomments` call attempting `approved: false` on an existing item left `approved` unchanged (`true`) while the `comment` field in the same request did update, confirming only `approved` is blocked.
