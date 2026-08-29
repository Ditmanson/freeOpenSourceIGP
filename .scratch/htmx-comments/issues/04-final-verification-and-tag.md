# 04: Final live verification, cleanup, and tag

**What to build:** The htmx rewrite is verified end-to-end on the live, deployed site, confirmed-stale backup files are cleaned up if appropriate, and a new release is tagged.

**Blocked by:** 02, 03

**Status:** ready-for-agent

- [ ] `public/` is rebuilt (`rm -rf public/* && hugo`) and committed, per the deploy process documented in `docs/deploys.md`
- [ ] Changes are pushed and the Amplify deploy is confirmed to succeed
- [ ] On the live site: an existing post's comments still load and render correctly; a post with no comments shows the empty state correctly; submitting a comment (with a solved widget) still works end-to-end and shows the new success + review-schedule messages; the captcha error states from Issue 2 still work correctly
- [ ] `layouts/_partials/bak/comments.html.bak` and `layouts/_partials/bak/postComment.html.bak` are reviewed - if confirmed to be pre-AppSync-migration artifacts with no remaining reference value, they're deleted; if there's any doubt, they're left in place rather than guessed at. `comments_htmx_dontwork.html` is left in place either way (explicit historical reference per the spec)
- [ ] This is the point at which the site owner decides whether to tag a new release
