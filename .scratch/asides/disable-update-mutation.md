# Aside: disable updateGrizcomments entirely

Not part of a formal ticket - a quick standalone fix, same pattern as the ticket 02 approved-stripping addition.

**Finding:** `updateGrizcomments` allowed any holder of the public API key to overwrite `comment`/`name`/`url` on any existing comment (including live, approved ones) via direct GraphQL calls - a defacement vector, unrelated to bot/captcha scope. `postSlug`/`createdAt` (the required key) are discoverable via `listGrizcomments`. No client code ever called this mutation.

**Fix:** `Mutation.updateGrizcomments`'s resolver `request()` now calls `util.error('updateGrizcomments is disabled', 'Unauthorized')` immediately, before ever reaching the DynamoDB data source. No field is updatable via this mutation anymore.

**Verified live:** a mutation attempting to overwrite the `comment` field on a real, existing approved item returned `Unauthorized` / "updateGrizcomments is disabled", and a follow-up `get-item` confirmed the comment's text is unchanged.

No repo/application files change - AWS resolver state only.
