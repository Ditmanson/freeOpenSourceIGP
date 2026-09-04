# 06: Final live verification, push, and tag

**What to build:** The full chatbot feature verified end-to-end on the live, deployed site, including deliberately exercising the safety limits, before tagging a release.

**Blocked by:** 04, 05

**Status:** done

- [x] `public/` rebuilt per `docs/deploys.md` (`rm -rf public/* && hugo`), committed (`07f5aea`), pushed, and the Amplify deploy confirmed `SUCCEED` (job 30, polled via `aws amplify get-job` rather than assumed from the push alone)
- [x] On the live site: a real question on the homepage (`https://griz.sh/`) gets a real, grounded answer with real post links, verified in an actual browser (Playwright/Chromium) against production, not curl or a local dev server; the widget markup is confirmed absent from `/dogs/`
- [x] A deliberate rate-limit test against the live Function URL (12 rapid requests, same approach as ticket 02/04) confirms the visitor-facing rejection message, both at the API level (curl) and rendered in the live widget UI (distinct `has-text-warning` styling from ticket 05); polling `describe-alarms` promptly afterward (learning from ticket 04's timing miss) caught a real live `ALARM` transition quoting the actual datapoint
- [x] Confirmed email/calendar tools remain disabled by default on the live deployment - not just in the local repo, but by downloading and inspecting the actually-deployed Lambda code's `capabilities.json` via `aws lambda get-function --query Code.Location`. Also proved the single-file mechanism is genuinely sufficient: temporarily flipped `send_email.enabled` to `true`, redeployed, and confirmed live that the model now attempts to use it (its answer referenced the tool's own "not implemented... placeholder for future capability" result) - then reverted to the real committed config and redeployed, re-verified live that the deployed code matches git exactly
- [x] This is the point at which the site owner decides whether to tag a new release

**Real bug found and fixed during live verification - the reason this ticket exists as a separate step, not just a formality:**

The first live browser test against `https://griz.sh/` failed with a genuine CORS preflight rejection, even though the Function URL's CORS config already listed `https://griz.sh` as an allowed origin (set correctly back in ticket 01). Root cause: htmx automatically attaches its own headers to every request (`HX-Request`, `HX-Trigger`, `HX-Target`, `HX-Current-URL`), but the Function URL's `AllowHeaders` only listed `content-type` - so the real browser preflight (which requests permission for the full header set) failed silently, while a simplified curl-simulated preflight (which didn't ask for those headers) misleadingly succeeded.

Ticket 05's testing didn't catch this because verification there either ran with CORS enforcement disabled entirely (`--disable-web-security`, to get past `localhost` not being the allowed origin) or failed on origin mismatch before ever reaching a real preflight against the actual allowed origin - neither path exercised the full, real header set a genuine `https://griz.sh` request sends. This is exactly what live verification against the actual deployed origin exists to catch.

Fixed by capturing the real request headers via Playwright's network inspection (`hx-trigger`, `hx-target`, `hx-current-url`, `hx-request`, alongside the existing `content-type`) and adding them to the Function URL's `AllowHeaders` via `aws lambda update-function-url-config`. Re-verified live immediately after: the same question that failed with a CORS error now returns a real HTTP 200 with a grounded answer rendered correctly in the widget.

**Design notes:** the per-IP rate-limit counter used for live verification was reset once mid-test (via a direct DynamoDB `UpdateItem` on my own test IP's hour-bucket key) purely to avoid waiting ~25 minutes for the real hourly bucket to roll over - this only affects my own test traffic's count, not any real visitor's, and the TTL still expires the bucket naturally. Real tracked monthly spend after all of this session's testing is ~$0.034, far under the $10 ceiling.
