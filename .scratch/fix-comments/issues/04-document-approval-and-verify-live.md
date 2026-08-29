# 04: Document approval workflow and verify end-to-end on the live site

**What to build:** The exact command the site owner runs to approve a pending comment is written down somewhere durable in the repo. The full fix is then verified end-to-end against the live, deployed site (not just direct API calls) as the final check before the site owner tags a release.

**Blocked by:** 01, 02, 03 (needs a working key, server-side moderation enforcement, and a clean table to do a meaningful end-to-end test)

**Status:** done

- [x] The exact `aws dynamodb update-item` command to flip a specific comment's `approved` to `true`, parameterized by `postSlug` and `createdAt`, is documented in the repo — `docs/comment-moderation.md` (note: the AppSync `updateGrizcomments` mutation alternative mentioned in the original ticket text is explicitly NOT viable — ticket 02 deliberately stripped `approved` from what that mutation can set, so direct DynamoDB access is the only path)
- [x] Changes from tickets 01–03 are committed and pushed so the live site picks up the new API key — required an additional, previously-unplanned step: AWS Amplify's build for this app doesn't run `hugo build`, it deploys `public/` verbatim, so `public/` had to be manually rebuilt (`rm -rf public/* && hugo`) and committed/pushed separately before the layouts/resolver fixes actually reached the live site. This is now documented in `docs/comment-moderation.md` under "A note on deploys" so it isn't rediscovered painfully next time.
- [x] After the live site updates, a real comment is submitted through the on-page form on a live post — submitted on `https://griz.sh/tech/k3s-setup/` by the site owner
- [x] The submitted comment is confirmed NOT visible on the page (moderation gate working) — confirmed both visually by the site owner and via a direct table scan showing the item with `approved: false`
- [x] The documented approval command is run against that specific comment
- [x] The comment is confirmed to become visible on the page after approval, without needing another deploy — confirmed by the site owner on refresh
- [x] Existing (previously working) comment display/posting behavior is otherwise unchanged from the site visitor's perspective, aside from the moderation delay
- [x] This is the point at which the site owner checks the live site directly and decides whether to tag a new release — tagging `v1.1.0`

**UX gap noted for a follow-up issue (not this one):** on successful submission, the form just silently resets — there's no "submitted for review" confirmation message, so from the visitor's perspective it can look like nothing happened. Flagged by the site owner during live testing.

**Unrelated observation from live testing, not investigated further:** the site owner saw a browser ad-blocker (YouTube-ad-focused) flag something as blocked in devtools network tab while testing on `/tech/k3s-setup/`, which has a YouTube embed. Very likely the ad blocker flagging the YouTube iframe itself, unrelated to the comments fix — the comment flow was independently confirmed working end-to-end via direct table checks regardless.
