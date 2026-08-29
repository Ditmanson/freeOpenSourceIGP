#!/usr/bin/env python3
"""List pending (approved:false) comments from the grizcomments table into a YAML file for review."""

import argparse
import json
import subprocess
import sys

import yaml

TABLE_NAME = "grizcomments"
REGION = "us-east-2"


def scan_unapproved():
    items = []
    start_key = None
    while True:
        cmd = [
            "aws", "dynamodb", "scan",
            "--table-name", TABLE_NAME,
            "--region", REGION,
            "--filter-expression", "approved = :false",
            "--expression-attribute-values", '{":false":{"BOOL":false}}',
        ]
        if start_key:
            cmd += ["--exclusive-start-key", json.dumps(start_key)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"aws dynamodb scan failed:\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        page = json.loads(result.stdout)
        items.extend(page["Items"])
        start_key = page.get("LastEvaluatedKey")
        if not start_key:
            break
    return items


def from_dynamodb_item(item):
    plain = {}
    for key, wrapped in item.items():
        if "S" in wrapped:
            plain[key] = wrapped["S"]
        elif "BOOL" in wrapped:
            plain[key] = wrapped["BOOL"]
        else:
            raise ValueError(f"unhandled DynamoDB type for {key!r}: {wrapped!r}")
    return plain


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", default="pending-comments.yaml",
        help="path to write the YAML file (default: pending-comments.yaml)",
    )
    args = parser.parse_args()

    items = [from_dynamodb_item(item) for item in scan_unapproved()]
    items.sort(key=lambda c: (c["postSlug"], c["createdAt"]))

    with open(args.output, "w") as f:
        yaml.safe_dump(items, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    print(f"{len(items)} pending comment(s) written to {args.output}")
    print("Flip `approved: true` on any entries you want to approve, then run approve-comments.py")


if __name__ == "__main__":
    main()
