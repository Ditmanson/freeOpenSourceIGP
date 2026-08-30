# 02: Rate limiting and spend circuit-breaker

**What to build:** The cost-safety net the site owner explicitly prioritized, added to the Lambda before any richer/more expensive capability is built on top of it. A new DynamoDB table tracks per-IP request counts (short TTL) and a running global spend/token total; the Lambda enforces both, rejecting requests that exceed either.

**Blocked by:** 01

**Status:** done

- [x] New DynamoDB table `chatbot-limits` (pay-per-request billing, matching `grizcomments`), TTL enabled on a `ttl` attribute
- [x] Per-IP request count enforced via a fixed-hour bucket key (`ip#<ip>#<hour>`), atomically incremented with `if_not_exists` TTL-set-once semantics - exceeding `MAX_REQUESTS_PER_IP_PER_HOUR` (10) returns a clear 429 with a human-readable message, not a silent drop
- [x] Global monthly spend ceiling (`MONTHLY_SPEND_CEILING_USD`, $10) enforced via a per-month bucket key (`spend#<YYYY-MM>`), checked *before* the per-IP check and before any Bedrock call - crossing it refuses all requests regardless of IP, with its own distinct message
- [x] Input length cap (`MAX_INPUT_CHARS`, 1000) rejects oversized questions before ever calling Bedrock; output cap (`MAX_OUTPUT_TOKENS`, 300) passed as `max_tokens` to the model
- [x] All four thresholds are named constants at the top of `handler.py` under a clearly labeled "Tunable limits" section - editing them is the whole mechanism, no other code changes needed
- [x] Every mutating AWS command (table creation, TTL config, IAM policy update, Lambda code update) was run without per-command confirmation this session, per explicit instruction
- [x] Verified via repeated direct `curl` calls: a normal request succeeds and both tracking items appear correctly in DynamoDB; 12 rapid requests from the same IP succeed exactly 10 times then correctly 429 from request 11 onward, with the DynamoDB item's `count` confirming every attempt (including rejected ones) increments; the monthly spend ceiling was verified by temporarily setting the tracked spend above $10 directly in DynamoDB (to avoid actually spending $10 to test it), confirming the distinct "monthly usage limit" message fires and takes priority over the per-IP check, then restoring the real tracked value; the input-length cap was verified with a 1500-character question correctly rejected before any Bedrock call
- [x] No changes to `public/`

**Design notes:** rejected requests still increment the per-IP counter (intentional - a bot hammering past the limit doesn't get free re-attempts). Actual per-request cost during this ticket's testing (~$0.00004/request) is far below the earlier ~$0.005/request estimate because there's no site-content context yet (ticket 03) - the tracking mechanism itself is verified correct and will scale to real per-request costs once that context is added.

**Code review caught a real race condition, fixed before ship:** the original spend-ceiling check was read-then-write across two separate DynamoDB calls (check current total, call Bedrock, then record spend afterward) - a burst of concurrent requests could all read the same pre-crossing total, all pass the check, and collectively overspend past the ceiling before any of them recorded spend. The sequential curl testing in the first pass couldn't have caught this (both reviewers flagged it independently).

Fixed with a reserve-then-true-up pattern: before calling Bedrock, the Lambda atomically reserves this request's *worst-case* cost (`_MAX_REQUEST_COST_MICRODOLLARS`, computed from `MAX_INPUT_CHARS`/`MAX_OUTPUT_TOKENS`) via a single conditional `UpdateItem` (`ConditionExpression` checks the pre-update value, so DynamoDB itself serializes concurrent attempts - no separate read). If the reservation would cross the ceiling, the conditional check fails atomically and the request is rejected before ever calling Bedrock. After the real response comes back, `_true_up_monthly_spend` corrects the ledger from the worst-case reservation down to the actual token cost (or refunds it fully if Bedrock itself failed).

**Re-verified under genuine concurrency, not just sequential requests:** set the tracked spend to leave room for exactly one more reservation, then fired 5 truly concurrent `curl` requests in parallel (backgrounded, `wait`ed together). Exactly 1 of 5 succeeded; the other 4 correctly got the monthly-limit rejection - direct proof the atomic reservation serializes concurrent requests correctly, not just theoretically. The artificially-inflated spend value used for this test was reset back to a small value reflecting only genuine test usage afterward, so the real ceiling isn't artificially pre-consumed for the rest of the month.
