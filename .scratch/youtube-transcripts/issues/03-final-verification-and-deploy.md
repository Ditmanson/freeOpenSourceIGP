# 03: Final live verification, push, and tag decision

**What to build:** The full transcripts feature verified end-to-end on the live, deployed site before deciding whether to tag a release.

**Blocked by:** 02

**Status:** done

- [x] `public/` rebuilt (`rm -rf public/* && hugo`) per `docs/deploys.md`, committed (`d6c6bc4`), pushed, and the Amplify deploy confirmed `SUCCEED` via `aws amplify list-jobs` (not just assumed from the push)
- [x] On the live site (`https://griz.sh/dogs/gear/`): confirmed a real 6-video post shows exactly one "Youtube Transcripts" section header with 6 correctly-titled sub-headers, verified via both `curl` and a real Playwright/Chromium browser against production; `https://griz.sh/dogs/igp_rules/` (no embedded video) confirmed to show zero occurrences
- [x] On the live site: asked the chatbot "Is there a video where someone named Anastasia is mentioned or praised during training?" - "Anastasia" appears only in a video transcript (`aA91Hw7MDYo`, embedded on `griz-5-months-puppy-sleeve`), never in that post's own prose (checked the source file directly). The live chatbot correctly answered, citing that exact post and describing what happens in the video - proving the content-index integration is genuinely grounded in transcript content live, not just working at build time
- [x] This is the point at which the site owner decides whether to tag a new release
