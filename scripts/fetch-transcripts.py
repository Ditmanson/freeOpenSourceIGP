#!/usr/bin/env python3
"""Fetch YouTube auto-captions and titles for every video embedded in content/,
writing one JSON file per video to data/transcripts/ for Hugo to read at build time."""

import argparse
import functools
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
TRANSCRIPTS_DIR = REPO_ROOT / "data" / "transcripts"

SHORTCODE_RE = re.compile(r"\{\{\s*<\s*youtube\s+([A-Za-z0-9_-]{11})\s*>\s*\}\}")
OEMBED_URL = "https://www.youtube.com/oembed?url={}&format=json"
REQUEST_TIMEOUT_SECONDS = 10

# youtube_transcript_api's own HTTP calls have no built-in timeout - without
# this, a hung connection could block the whole script indefinitely with no
# way to bound it from the caller side. requests.Session has no timeout
# param of its own, so this is the standard idiom for giving one a default.
_transcript_session = requests.Session()
_transcript_session.request = functools.partial(
    _transcript_session.request, timeout=REQUEST_TIMEOUT_SECONDS
)


def find_video_ids():
    ids = set()
    for path in CONTENT_DIR.rglob("*.md"):
        ids.update(SHORTCODE_RE.findall(path.read_text()))
    return sorted(ids)


def fetch_title(video_id):
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    url = OEMBED_URL.format(urllib.parse.quote(watch_url, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read())["title"]


def fetch_transcript_text(video_id):
    result = YouTubeTranscriptApi(http_client=_transcript_session).fetch(video_id)
    return " ".join(snippet.text.strip() for snippet in result.snippets if snippet.text.strip())


def fetch_one(video_id):
    title = fetch_title(video_id)
    transcript = fetch_transcript_text(video_id)
    return {"video_id": video_id, "title": title, "transcript": transcript}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="re-fetch every video, including ones already in data/transcripts/",
    )
    args = parser.parse_args()

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    video_ids = find_video_ids()
    print(f"Found {len(video_ids)} video ID(s) referenced in content/")

    fetched, skipped, no_captions, failed = 0, 0, 0, 0
    for video_id in video_ids:
        out_path = TRANSCRIPTS_DIR / f"{video_id}.json"
        if out_path.exists() and not args.force:
            skipped += 1
            continue

        try:
            data = fetch_one(video_id)
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            print(f"  {video_id}: no captions available ({e.__class__.__name__}) - skipped", file=sys.stderr)
            no_captions += 1
            continue
        except Exception as e:
            print(f"  {video_id}: fetch failed ({e}) - skipped", file=sys.stderr)
            failed += 1
            continue

        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"  {video_id}: wrote {out_path.relative_to(REPO_ROOT)} ({len(data['transcript'])} chars)")
        fetched += 1

    print(
        f"Done: {fetched} fetched, {skipped} already present, "
        f"{no_captions} no captions available, {failed} failed"
    )


if __name__ == "__main__":
    main()
