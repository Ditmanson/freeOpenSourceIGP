# Comment approval scripts

Bulk alternative to the single-comment `aws dynamodb update-item` flow in `docs/comment-moderation.md` — review a batch of pending comments in one YAML file, then push approvals in one go.

## Setup (one-time)

```
cd scripts
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Usage

```
./.venv/bin/python list-unapproved-comments.py
```

Writes every `approved:false` comment in the `grizcomments` table to `pending-comments.yaml` (gitignored). Open it, and flip `approved: true` on whichever entries you want to approve — leave the rest as `false`.

```
./.venv/bin/python approve-comments.py
```

Reads `pending-comments.yaml`, shows you what it's about to approve, asks for confirmation, then pushes `approved: true` to DynamoDB for each entry you flipped. Entries left as `false` are skipped (not deleted, not denied — just left pending for a future run). Pass `--yes` to skip the confirmation prompt.

Both scripts only touch the `approved` field — nothing else about a comment can be edited this way.

## Transcript fetching

```
./.venv/bin/python fetch-transcripts.py
```

Scans `content/` for `{{< youtube VIDEO_ID >}}` shortcodes, and for any video ID not already present under `data/transcripts/`, fetches its title (YouTube oEmbed) and auto-caption transcript (`youtube-transcript-api`) and writes `data/transcripts/<video_id>.json`. Run this after adding a new post with an embedded video, then rebuild `public/` per `docs/deploys.md` as usual.

A video with no captions available is skipped with a message, not a failure — the run continues to the rest. Pass `--force` to re-fetch every video, including ones already written.
