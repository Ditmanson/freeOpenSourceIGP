# 04: CloudWatch alarm and notification for limit-hit events

**What to build:** The site owner is notified when the chatbot rejects a request for hitting a rate limit or the spend ceiling, using the same alarm/notification path already relied on for the AppSync alarms - not a new, separate notification mechanism.

**Blocked by:** 02 (only needs the rate-limit/circuit-breaker logic to exist, not the fuller capabilities from ticket 03)

**Status:** ready-for-agent

- [ ] The Lambda publishes a custom CloudWatch metric when it rejects a request for a rate-limit or spend-ceiling reason (distinguishing the two reasons if reasonably easy, not required if it complicates things)
- [ ] A CloudWatch alarm on that metric is wired to the existing SNS topic (`grizsh`) already used for the AppSync 4xx/5xx/latency alarms - no new notification channel is introduced
- [ ] Every mutating AWS command (the metric publishing permission if needed, the alarm itself) is surfaced to the site owner for confirmation before it runs
- [ ] Verified by deliberately triggering a rate-limit rejection (reusing the same approach from ticket 02's verification) and confirming the metric/alarm actually reflects it - not just confirming the alarm exists unconfigured
- [ ] No changes to `public/`
