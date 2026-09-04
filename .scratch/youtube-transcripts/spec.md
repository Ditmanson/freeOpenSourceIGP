Status: ready-for-agent

# Show YouTube transcripts at the bottom of pages with embedded videos

## Problem Statement

Pages on the site embed YouTube training videos via Hugo's built-in `youtube` shortcode, but the video content itself is invisible to anything that can't watch video - text search (including the site's own chatbot), screen readers, and visitors who'd rather skim text than watch a clip all get nothing from an embedded video beyond its surrounding prose. There's no transcript anywhere on the page.

## Solution

Any page containing one or more `{{< youtube VIDEO_ID >}}` shortcodes gets a "Youtube Transcripts" section appended at the bottom, below the existing content/comments. For each embedded video on that page, the section shows the video's own YouTube title as a sub-header, followed by its transcript text. Pages with no embedded video render nothing extra.

Transcript text and titles are fetched once per video (via YouTube's public auto-caption and oEmbed endpoints - no API key, no new AWS resource) by a new script under `scripts/`, following the same manual/local-tooling pattern already established there (`approve-comments.py`, `list-unapproved-comments.py`). Fetched data is written to committed Hugo data files under `data/transcripts/`, which Hugo reads at build time - no runtime fetching, no new build-time external dependency, consistent with `docs/deploys.md`'s existing "rebuild `public/` locally, then commit and push" workflow.

## User Stories

1. As a site visitor reading a post with an embedded video, I want to read a transcript of that video below the page content, so that I can get the information without watching the whole clip.
2. As a site visitor using a screen reader, I want the video's spoken content available as text, so that an embedded video isn't a dead end.
3. As a site visitor on a page with multiple embedded videos, I want a distinct transcript (with its own title) for each video, so that I can tell which transcript belongs to which clip.
4. As a site visitor on a page with no embedded video, I want no "Youtube Transcripts" section at all, so that the page isn't cluttered with an empty or irrelevant heading.
5. As the site owner, I want the transcript section's sub-header to show the video's real YouTube title, so that it's identifiable even out of context (e.g. if the post's own title doesn't match the video's).
6. As the site owner, I want transcripts fetched by a script I run manually (like the existing comment-moderation scripts), so that a new post with a video is a two-step "write the post, run the transcript script" workflow rather than something that silently depends on an external service at every build.
7. As the site owner, I want fetched transcripts committed to the repo as Hugo data files, so that `hugo` builds stay fast, offline-capable, and don't re-fetch unchanged transcripts every time.
8. As the site owner, I want a video with no available captions handled gracefully (skipped with a clear message from the script), so that one uncaptioned video doesn't break the build or the script run for every other video.
9. As the site owner, I want the script to only fetch videos it doesn't already have a transcript for by default, so that re-running it after adding one new post doesn't waste time re-fetching everything.
10. As the site owner, I want the chatbot's site content index (`layouts/index.json.json`, from the earlier AI chatbot feature) to include transcript text where available, so that the chatbot can answer questions grounded in what's actually said in a video, not just the surrounding post text.

## Implementation Decisions

- **Transcript source**: YouTube's public auto-generated-caption mechanism, accessed via the `youtube-transcript-api` Python library (no API key, no OAuth, no new AWS resource or cost). Confirmed working against this site's actual videos during spec discussion.
- **Title source**: YouTube's public oEmbed endpoint (`https://www.youtube.com/oembed?url=...&format=json`), also free and keyless, fetched alongside the transcript for the same video ID.
- **New script**: `scripts/fetch-transcripts.py`, following the existing `scripts/` conventions (argparse CLI, a `requirements.txt` entry, README update). Scans `content/` for `{{< youtube VIDEO_ID >}}` shortcode usages (regex, not a full Hugo parse) to build the set of video IDs in use, fetches any not already present under `data/transcripts/`, and writes one JSON file per video ID (e.g. `data/transcripts/QcWcQG2hU0Y.json`) containing at least the video's title and full transcript text. A `--force` flag re-fetches everything, matching the "only fetch what's missing by default" story above.
- **Hugo integration**: a new partial (e.g. `layouts/_partials/youtubeTranscripts.html`), included from `layouts/page.html` (the only template that currently renders post content/comments), that: (a) extracts the video IDs used on the current page via `.HasShortcode "youtube"` plus a regex/parse over `.RawContent` (Hugo doesn't expose shortcode arguments directly, so the same video-ID-extraction approach used by the fetch script needs a page-side equivalent - implementer should confirm the cleanest available Hugo mechanism here), (b) looks up each ID in `.Site.Data.transcripts`, (c) renders the "Youtube Transcripts" header once, then one sub-header + transcript block per video found. Renders nothing if the page has no video or no matching transcript data.
- **Chatbot content index integration**: `layouts/index.json.json` (from the chatbot feature) gains transcript text in its per-page `summary`/a new field, sourced the same way as the display partial, so the existing chatbot search/grounding logic benefits without any Lambda-side changes.
- **Data shape** (illustrative, from the working spike during spec discussion):
  ```json
  {
    "video_id": "QcWcQG2hU0Y",
    "title": "...",
    "transcript": "full transcript text, whitespace-joined from caption snippets"
  }
  ```

## Testing Decisions

- A good test here checks external behavior: given a page with a known `{{< youtube ID >}}` shortcode and a corresponding `data/transcripts/ID.json` fixture, the rendered HTML contains the expected header, sub-header (video title), and transcript text; given a page with no shortcode, no such section appears.
- `scripts/fetch-transcripts.py` should be tested the way the existing `scripts/` tooling is used/verified - run against real video IDs and inspect the written output - rather than a mocked unit-test suite, matching this repo's existing lack of a test framework for its Python scripts.
- No prior art for Hugo template testing exists in this repo (verification has consistently been "build with `hugo`, inspect `public/` output, check in a real browser" throughout every prior feature) - continue that pattern.

## Out of Scope

- Automatic/build-time transcript fetching (explicitly rejected in favor of the manual script workflow).
- Translating or editing transcripts for readability (auto-caption text is used as-is).
- Handling videos that are not the site owner's own uploads, or any embed mechanism other than the existing `youtube` shortcode.
- A UI for browsing/searching transcripts independent of their source page.
- Updating already-published posts' `public/` output as part of this feature's implementation - per every prior feature on this site, `public/` is rebuilt and pushed as an explicit final step, not silently.

## Further Notes

`youtube-transcript-api` and the oEmbed endpoint are both unofficial/undocumented-contract public mechanisms (not a formal, versioned YouTube API), so the fetch script should fail clearly and per-video (not crash the whole run) if YouTube changes something - this is explicitly accepted risk for a free, keyless approach, matching the site owner's general cost-conscious posture on this project.
