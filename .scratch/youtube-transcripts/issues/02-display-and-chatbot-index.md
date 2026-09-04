# 02: Render transcripts on-page and feed them into the chatbot's content index

**What to build:** A real visitor sees a "Youtube Transcripts" section at the bottom of any page with an embedded video, and the chatbot's grounding data includes transcript text so it can answer questions about what's actually said in a video.

**Blocked by:** 01 (needs real fetched transcript data to render/index against)

**Status:** ready-for-agent

- [ ] A new partial (`layouts/_partials/youtubeTranscripts.html`) renders a "Youtube Transcripts" header, then one sub-header (the video's real YouTube title) + transcript block per distinct video embedded on the current page, sourced from `.Site.Data.transcripts`
- [ ] Included from `layouts/page.html` (the only template that renders post content), positioned below the existing content/comments
- [ ] A page with no embedded video, or whose embedded video(s) have no matching transcript data, renders no extra section at all - not an empty heading
- [ ] A page with multiple embedded videos gets a distinct, correctly-titled sub-header + transcript for each one
- [ ] `layouts/index.json.json` (the chatbot's build-time content index) incorporates transcript text where available for a page, so `search_site_content` can match against what's actually said in a video, not just the surrounding post prose
- [ ] Verified with `hugo` + inspecting `public/` output for at least one real post with a known video and known transcript fixture; verified in a real browser that the section renders correctly and a page without a video shows nothing extra
- [ ] Verified the chatbot content-index change end to end: rebuild the index locally, confirm transcript text appears in the generated JSON for a page that has one
- [ ] No AWS/Lambda-side changes (the chatbot Lambda already fetches and searches whatever `index.json` contains - this ticket only changes what Hugo puts into it)
- [ ] No changes to `public/` pushed live as part of this ticket (final rebuild/push happens in the next ticket)
