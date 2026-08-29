# 03: Final live verification, push, and tag

**What to build:** The full captcha chain is verified end-to-end on the live, deployed site (not just locally/directly against AppSync), and a new release is tagged once confirmed.

**Blocked by:** 02

**Status:** done

- [x] `public/` is rebuilt (`rm -rf public/* && hugo`) and committed (`7307e02`), following the `postComment.html` widget change (`515ab2f`)
- [x] Changes are pushed and the Amplify deploy is confirmed to succeed — job 15, commit `7307e02`, `SUCCEED`
- [x] On the live site, the site owner solved the real widget (auto-passed in Managed mode, spinner then green success) and submitted a comment through the actual form; confirmed via table scan: `"Posting a test comment to test out my captcha"` landed on `/tech/k3s-setup/` with `approved: false`
- [x] A raw `curl` `createGrizcomments` call with no Turnstile token, against the live real-key resolver, is confirmed rejected (`Unauthorized`/"Turnstile verification failed"), with a follow-up check confirming nothing was written
- [x] Existing comment-viewing and previously-working submission behavior (aside from the new captcha gate) is confirmed unchanged — a live `listGrizcomments` query correctly returns all 3 items (2 approved, 1 pending) with their real `approved` states intact; `comments.html` untouched since `3a0a819`
- [ ] Tag `v1.2.0` — not yet created; happens after this ticket file is committed, per the same order used in Issues 1 and 2
