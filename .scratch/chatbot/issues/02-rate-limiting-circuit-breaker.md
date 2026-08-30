# 02: Rate limiting and spend circuit-breaker

**What to build:** The cost-safety net the site owner explicitly prioritized, added to the Lambda before any richer/more expensive capability is built on top of it. A new DynamoDB table tracks per-IP request counts (short TTL) and a running global spend/token total; the Lambda enforces both, rejecting requests that exceed either.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] A new DynamoDB table exists (pay-per-request billing, matching `grizcomments`) for rate-limit/spend tracking
- [ ] The Lambda tracks and enforces a per-IP request count within a rolling time window, using a short TTL on tracking items - a visitor IP exceeding the threshold gets a clear "rate limited" response, not a silent drop or a broken response
- [ ] The Lambda tracks and enforces a global spend/token ceiling (e.g. per day or per month) independent of which IP is asking - once crossed, *all* requests are refused until the tracking period resets, closing the gap where many distinct IPs could otherwise bypass per-IP limiting
- [ ] The Lambda enforces a cap on input length (rejects oversized questions before calling Bedrock) and a cap on output tokens requested from the model
- [ ] All thresholds (per-IP limit, window size, global ceiling, input/output caps) are easy to find and tune, not scattered/hardcoded deep in unrelated logic
- [ ] Every mutating AWS command (the new table) is surfaced to the site owner for confirmation before it runs
- [ ] Verified via repeated direct `curl` calls to the Function URL: exceeding the per-IP threshold results in a rate-limited response, and the DynamoDB table's actual state (item counts, TTLs) is inspected to confirm it matches what the Lambda enforced, not just trusted from the response alone
- [ ] No changes to `public/`
