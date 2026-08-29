#!/usr/bin/env python3
"""Read a YAML file produced by list-unapproved-comments.py and push approved:true
flips back to the grizcomments table. Entries left as approved:false are skipped."""

import argparse
import json
import subprocess
import sys

import yaml

TABLE_NAME = "grizcomments"
REGION = "us-east-2"


def approve_item(post_slug, created_at):
    key = json.dumps({
        "postSlug": {"S": post_slug},
        "createdAt": {"S": created_at},
    })
    result = subprocess.run(
        [
            "aws", "dynamodb", "update-item",
            "--table-name", TABLE_NAME,
            "--region", REGION,
            "--key", key,
            "--update-expression", "SET approved = :true",
            "--expression-attribute-values", '{":true":{"BOOL":true}}',
        ],
        capture_output=True, text=True,
    )
    return result.returncode == 0, result.stderr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i", "--input", default="pending-comments.yaml",
        help="path to the YAML file to read (default: pending-comments.yaml)",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="skip the confirmation prompt",
    )
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            items = yaml.safe_load(f) or []
    except FileNotFoundError:
        print(f"{args.input} not found. Run list-unapproved-comments.py first.", file=sys.stderr)
        sys.exit(1)

    to_approve = [c for c in items if c.get("approved") is True]
    skipped = len(items) - len(to_approve)

    if not to_approve:
        print(f"Nothing to do: 0 of {len(items)} entries are flipped to approved:true.")
        return

    print(f"About to approve {len(to_approve)} comment(s) ({skipped} left pending):")
    for c in to_approve:
        preview = c.get("comment", "")[:60]
        print(f"  - {c['postSlug']}  [{c.get('name', '?')}] {preview!r}")

    if not args.yes:
        reply = input("Push these approvals? [y/N] ").strip().lower()
        if reply != "y":
            print("Aborted, nothing changed.")
            return

    failures = []
    for c in to_approve:
        ok, err = approve_item(c["postSlug"], c["createdAt"])
        if ok:
            print(f"  approved: {c['postSlug']} @ {c['createdAt']}")
        else:
            print(f"  FAILED: {c['postSlug']} @ {c['createdAt']}: {err}", file=sys.stderr)
            failures.append(c)

    print(f"\n{len(to_approve) - len(failures)}/{len(to_approve)} approved.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
