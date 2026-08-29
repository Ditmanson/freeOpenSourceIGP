# 03: Final live verification, push, and tag

**What to build:** The full captcha chain is verified end-to-end on the live, deployed site (not just locally/directly against AppSync), and a new release is tagged once confirmed.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] `public/` is rebuilt (`rm -rf public/* && hugo`) and committed alongside the `postComment.html` changes — remembering the Issue-1-discovered gotcha that AWS Amplify's build for this app doesn't run `hugo build`, it just deploys whatever is already committed in `public/`
- [ ] Changes are pushed and the Amplify deploy is confirmed to succeed
- [ ] On the live site, the site owner solves the real widget and submits a comment through the actual form; the comment is confirmed to land with `approved: false` (via a table check), same as the rest of the moderation flow from Issue 1
- [ ] A raw `curl` `createGrizcomments` call with no/garbage Turnstile token, against the live (real-key, not dummy) resolver, is confirmed rejected
- [ ] Existing comment-viewing and previously-working submission behavior (aside from the new captcha gate) is confirmed unchanged from a site visitor's perspective
- [ ] This is the point at which the site owner decides whether to tag a new release
