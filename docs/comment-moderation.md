# Approving a pending comment

New comments land in the `grizcomments` DynamoDB table (region `us-east-2`) with `approved: false` by default — this is enforced server-side by the `createGrizcomments` AppSync resolver, not by the client, so it can't be bypassed by posting directly against the public API. The site's display query only shows comments where `approved: true`.

There's no approval UI. Requires the AWS CLI configured with credentials that have `dynamodb:Scan`/`dynamodb:UpdateItem` on the `grizcomments` table. To approve a specific comment:

1. Find the pending comment (optionally filter by post):

   ```
   aws dynamodb scan --table-name grizcomments --region us-east-2 \
     --filter-expression "approved = :false" \
     --expression-attribute-values '{":false":{"BOOL":false}}'
   ```

2. Note its `postSlug` and `createdAt` (the table's composite key), then approve it:

   ```
   aws dynamodb update-item --table-name grizcomments --region us-east-2 \
     --key '{"postSlug":{"S":"<postSlug>"},"createdAt":{"S":"<createdAt>"}}' \
     --update-expression "SET approved = :true" \
     --expression-attribute-values '{":true":{"BOOL":true}}'
   ```

The comment appears on the live page immediately — comments are fetched client-side on page load, so no rebuild or redeploy is needed.

Note: the `updateGrizcomments` GraphQL mutation deliberately cannot set `approved` (it's stripped server-side) — approval only works via direct DynamoDB access like the above, using your own AWS credentials, not the public API key.

Approving a comment takes effect immediately — no rebuild or redeploy needed, since comments are fetched client-side on page load. If you're also changing `content/`, `layouts/`, or `hugo.yaml`, see `docs/deploys.md` — this site's deploy step has a gotcha.
