# 04: Final live verification, cleanup, and tag

**What to build:** The htmx rewrite is verified end-to-end on the live, deployed site, confirmed-stale backup files are cleaned up if appropriate, and a new release is tagged.

**Scope note:** the "new success + review-schedule messages" verification item is void, same as ticket 03 - that messaging was dropped when the site owner switched to auto-approve mid-issue. See `.scratch/asides/auto-approve-comments.md` and ticket 03's scope-change note.

**Blocked by:** 02, 03

**Status:** done

- [x] `public/` is rebuilt and committed - done progressively across tickets 02/03/this ticket's predecessor commits, per `docs/deploys.md`; nothing in this ticket's own changes (bak-file deletion) affects build output, so no additional rebuild was needed here
- [x] Changes are pushed and each Amplify deploy confirmed to succeed - jobs 17-21, all `SUCCEED`
- [x] On the live site: comment loading/rendering, the empty state, posting end-to-end, and both captcha error states (unsolved widget, server-rejected token) were each confirmed live with the site owner's direct participation progressively across tickets 02 and 03, not re-tested as one redundant final pass here - structurally re-confirmed via the live page source for this ticket (`cf-turnstile`, `hx-post`, `buildCommentVals`, `selfRequestsOnly": false`, `refreshComments` all present)
- [x] `layouts/_partials/bak/comments.html.bak` and `layouts/_partials/bak/postComment.html.bak` reviewed and deleted - both confirmed to reference the old pre-AppSync `api.griz.sh/comments` REST endpoint, no remaining reference value. `comments_htmx_dontwork.html` left in place (explicit historical reference per the spec)
- [x] Tagging `v1.3.0`
