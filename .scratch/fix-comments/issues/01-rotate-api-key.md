# 01: Rotate API key and restore connectivity

**What to build:** The AppSync API key hardcoded in the commenting partials has been expired since 2026-07-04. A new, valid key is created on the `griz.sh comments` GraphQL API and put in place of the old one, restoring the ability to authenticate against the comments API at all.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] A new AppSync API key exists on API `3dlgu4u7cjg2pmp5zylj3zvcim` (region `us-east-2`) — `da2-zmx7kmlw7ze4hioupggncn3xtm`, expires 2027-08-29
- [x] Creating the key is surfaced to the site owner for confirmation before it runs (it's a mutating AWS call) — confirmed via chat before running `aws appsync create-api-key`
- [x] Both `comments.html` and `postComment.html` are updated to use the new key (endpoint URL is unchanged)
- [x] The old expired key is either left to expire/auto-delete per AppSync's normal lifecycle, or explicitly deleted — whichever is simpler; note which approach was taken — **left in place**, since it already fails auth (see below) and AppSync will auto-delete it per its own `deletes` timestamp (~2026-09-02)
- [x] A direct GraphQL request against the live AppSync endpoint (e.g. `listGrizcomments` via curl or `aws appsync`), authenticated with the new key, succeeds (no auth error) — curl `listGrizcomments` returned data (including the 2 stale items for ticket 03)
- [x] The same request using the old expired key fails auth, confirming the rotation actually took effect and isn't just coincidentally working — returned `UnauthorizedException`
- [x] No changes made to `public/` — this ticket only touches `layouts/_partials/`
