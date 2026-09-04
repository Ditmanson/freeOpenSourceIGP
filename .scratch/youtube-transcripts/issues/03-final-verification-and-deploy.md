# 03: Final live verification, push, and tag decision

**What to build:** The full transcripts feature verified end-to-end on the live, deployed site before deciding whether to tag a release.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] `public/` is rebuilt (`rm -rf public/* && hugo`) per `docs/deploys.md`, committed, and the Amplify deploy confirmed to succeed
- [ ] On the live site: at least one real post with an embedded video shows a correct "Youtube Transcripts" section with the real video title and transcript; a page with no embedded video is confirmed to show nothing extra
- [ ] On the live site: a chatbot question whose answer only exists in a video's spoken content (not the surrounding post text) gets a real, grounded answer - proving the content-index integration actually works live, not just at build time
- [ ] This is the point at which the site owner decides whether to tag a new release
