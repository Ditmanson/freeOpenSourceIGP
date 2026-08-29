# Aside: default new comments to approved:true (auto-approve)

Not part of a formal ticket - a direct policy change requested mid-way through the htmx-comments issue.

**Decision:** new comments are now auto-approved (`approved: true`) by default, reversing the moderation-gate default from Issue 1 (which forced `approved: false`). The site owner made this call deliberately, given captcha (Issue 2) is now also in place as a bot defense, and wants comments visible immediately rather than requiring manual approval for every post.

**Explicitly framed as reversible:** if spam becomes a real problem, revert the commit that made this change to restore the `approved: false` default. See the commit title/message for exactly what to revert.

**What did NOT change:**
- `updateGrizcomments` is still fully disabled for all clients (defacement protection from the earlier aside is unaffected).
- The Turnstile captcha gate (Issue 2) is unchanged and still required to post at all.
- `scripts/list-unapproved-comments.py` / `scripts/approve-comments.py` still work if manual moderation is ever turned back on.

**Verified live:** a mutation sending `approved: false` in its input still landed `approved: true` (server-side override, unchanged mechanism, just flipped value) - confirmed via a temporary swap to Cloudflare's dummy always-pass Turnstile key to isolate testing this from the unrelated captcha gate, then restored to the real secret and reconfirmed the captcha gate still correctly rejects invalid tokens.

No repo/application files change - AWS resolver state only.
