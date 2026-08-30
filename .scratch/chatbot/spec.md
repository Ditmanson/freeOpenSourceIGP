Status: ready-for-agent

# Add an AI chatbot search feature to the homepage

## Problem Statement

The site has no way for a visitor to ask a question and get pointed at relevant content - they have to browse `/dogs/`, `/tech/`, `/meetups/`, `/misc/`, or `/tags/` manually to find a post. The site owner wants a chatbot on the homepage that can search across the site's own content and point visitors at relevant posts and videos, without risking an open-ended AI bill if a bot or abusive user finds the endpoint and hammers it.

## Solution

A Lambda function, called via its own Function URL, backed by AWS Bedrock (Claude Haiku), answers visitor questions using a compact index of the site's own content (built at Hugo build time) so it can point people at relevant posts and videos. Every request is rate-limited per IP and against a hard spend/token circuit-breaker tracked in DynamoDB, so cost is bounded regardless of traffic. The chatbot's allowed capabilities (what it's permitted to do - initially just searching site content and surfacing video links) live in a single config file bundled with the Lambda, so the site owner can constrict or expand what it's allowed to do by editing one file and redeploying, without restructuring any code. Email and calendar capabilities are explicitly out of scope for this issue but are named in the config file's shape (disabled) so they're a natural extension later, not a redesign.

## User Stories

1. As a site visitor on the homepage, I want to ask a question in plain language, so that I can find relevant content without browsing manually.
2. As a site visitor, I want the chatbot to point me at specific posts and videos on the site (not answer from general knowledge), so that its answers are grounded in what's actually here.
3. As a site visitor, I want a reasonably fast, single response to my question (not a live-typing/streaming effect), so that the experience is simple and predictable.
4. As a site visitor who has asked a lot of questions in a short time, I want to be told I've hit a limit (not silently ignored or given a broken/blank response), so that I understand what happened.
5. As a site visitor browsing any page other than the homepage, I want the chatbot to simply not be present, so that it doesn't add weight/complexity to pages where it isn't offered.
6. As the site owner, I want per-IP rate limiting on chatbot requests, so that a single visitor (or bot) can't run up unbounded API cost on their own.
7. As the site owner, I want a hard, global spend/token ceiling that the Lambda enforces regardless of how many distinct IPs are involved, so that a distributed abuse pattern can't bypass per-IP limiting and still run up a large bill.
8. As the site owner, I want a cap on the size of a single request/response (input length and output token count), so that one oversized prompt or a runaway response can't itself be an expensive outlier.
9. As the site owner, I want to be notified when the chatbot hits a rate limit or spend ceiling, so that I know it's happening without having to check manually - using the same CloudWatch alarm -> SNS notification path already wired up for the AppSync alarms.
10. As the site owner, I want the chatbot's allowed capabilities (what actions/tools it can use) controlled by editing a single config file and redeploying, so that I can constrict or expand what it's allowed to do without touching the request-handling logic.
11. As the site owner, I want email and calendar capabilities to already exist as named (but disabled) entries in that same config file, so that enabling them later is a config change, not a rebuild of the capability system.
12. As the site owner, I want the Lambda to authenticate to Bedrock via its own IAM role, so that there's no separate API key/secret to store, rotate, or leak.
13. As the site owner, I want the site's content index (what the chatbot searches over) generated automatically at Hugo build time, so that it never goes stale relative to what's actually published.
14. As the site owner, I want prompt caching used for the repeated site-content context, so that cost per request is meaningfully lower than the naive per-request cost, for free.
15. As the site owner, I want every mutating AWS command (creating the Lambda, its IAM role, the DynamoDB rate-limit table, the Function URL, CloudWatch alarms) surfaced to me for confirmation before it runs, matching how every prior AWS-touching issue on this site has worked.
16. As the site owner, I want to verify the chatbot works correctly by calling the Lambda Function URL directly (not just through the homepage widget), so that request-handling/rate-limiting/capability logic can be tested independent of the UI.

## Implementation Decisions

- **LLM access**: AWS Bedrock, Claude Haiku (cheapest capable model, appropriate for a search-style feature). The Lambda's execution role is granted `bedrock:InvokeModel` (or equivalent) for the specific model - no Anthropic API key involved anywhere.
- **Endpoint**: a Lambda Function URL (not API Gateway) - avoids an unnecessary per-request-cost service for a low-traffic personal site. Auth type `NONE` (public), since the site itself is public and rate limiting happens inside the Lambda, not at the URL layer.
- **Non-streaming**: the Lambda returns one complete JSON response per request; no response streaming in this issue.
- **Rate limiting and spend control, tracked in a new DynamoDB table** (pay-per-request billing, matching `grizcomments`):
  - Per-IP request count with a short TTL (e.g. requests-in-the-last-hour, auto-expiring items) - a request over the per-IP threshold is rejected with a clear "rate limited" response, not silently dropped.
  - A running global spend/token total (e.g. tracked per day or per month) acting as a hard circuit-breaker - once crossed, the Lambda refuses *all* requests until the tracking period resets, regardless of which IP is asking.
  - Exact thresholds (requests/IP/window, global token/spend ceiling, max input length, max output tokens) are tunable values, not hardcoded deep in the handler logic - reasonable defaults are chosen at implementation time and documented, with the expectation the site owner may tune them after seeing real usage.
  - Storing visitor IP addresses for this purpose, with a short TTL and no long-term retention, is acceptable to the site owner (already confirmed).
- **Capability config file**: a single JSON file bundled with the Lambda deployment package defines the chatbot's available tools (Claude's tool-use/function-calling mechanism) as a list of `{name, description, enabled}` entries. At minimum: `search_site_content` and `list_videos`, both enabled. `send_email` and `check_calendar` (or similarly named) entries exist in the same file, `enabled: false`, establishing the shape for later expansion without a redesign. The Lambda's handler logic reads this file and only offers enabled tools to the model - disabling a tool in this file is sufficient to make the model unable to use it, without any handler code changes.
- **Site content index**: generated at Hugo build time as a Hugo custom output format (JSON) - the same mechanism commonly used for client-side search widgets (e.g. Lunr/Fuse.js-style search-index.json) - containing at minimum each page's title, URL, tags, and a short summary/excerpt. This file is bundled into the Lambda deployment (or fetched by the Lambda at invocation time from a location Hugo publishes it to) so the model has grounded, current site content to work from, without needing a vector database for a site this size.
- **Prompt caching**: the site-content-index context (identical across requests within its cache window) is sent as a cacheable prompt segment per Bedrock/Claude's prompt caching mechanism, reducing repeated-context cost.
- **Notifications**: the Lambda publishes a custom CloudWatch metric when it rejects a request for a rate-limit or spend-ceiling reason. A CloudWatch alarm on that metric, wired to the existing SNS topic (`grizsh`) already used for the AppSync alarms, notifies the site owner the same way the existing alarms do.
- **Homepage-only availability**: the chatbot widget is only rendered on the homepage (`layouts/home.html`, Hugo `Kind == "home"`). The existing `{{ if eq .Kind "page" }}` guard in `head.html` that loads htmx/Alpine/Mustache is extended (or paralleled) to also cover `Kind == "home"`, since the chatbot widget will use the same htmx/Alpine stack already established for comments.
- **Client-side widget**: built with htmx + Alpine, consistent with the comments feature - a request/response interaction against the Lambda Function URL, Alpine-driven UI state for loading/error/rate-limited states.
- **Deployment path**: the Lambda, its IAM role, the DynamoDB rate-limit table, the Function URL, and the CloudWatch alarm are all created via direct AWS CLI commands (matching how the AppSync resolvers, HTTP data source, and DynamoDB table were managed in prior issues) - not through the Amplify/git-triggered pipeline. Every mutating command is surfaced to the site owner for confirmation before running.
- **Lambda runtime**: Python (matching the existing `scripts/*.py` tooling's language choice, and Python's Lambda runtime ships `boto3` pre-installed, so no dependency packaging step is needed for a Bedrock-only Lambda).

## Testing Decisions

- No local dev harness exists for Lambda/Bedrock/DynamoDB in this repo, same as the AppSync work in prior issues.
- **Primary seam: direct HTTP requests to the Lambda Function URL** (via `curl`), independent of the homepage widget - this is where request-handling, capability gating, rate-limiting, and the spend circuit-breaker are actually verified, mirroring how the AppSync resolvers were tested via direct GraphQL calls in Issues 1-3.
- Rate-limit and circuit-breaker behavior is verified by making repeated direct calls and inspecting the DynamoDB tracking table's state, not just by trusting the code.
- After the Lambda-level behavior is verified directly, the homepage widget is verified in a real browser as the final end-to-end check, following the same rebuild-`public/`-and-push rhythm documented in `docs/deploys.md`.
- No automated test suite is expected - consistent with the rest of this repo.

## Out of Scope

- Email and calendar capabilities (explicitly deferred - only their config-file shape exists in this issue).
- Response streaming.
- API Gateway, WAF, or any other paid rate-limiting service - the DIY DynamoDB approach is the deliberate choice here, matching the cost-consciousness already established (e.g. choosing Turnstile over AWS WAF CAPTCHA).
- A vector database or embeddings-based search - the build-time JSON content index is considered proportionate for a site this size.
- Chatbot availability on any page other than the homepage.
- Conversation memory/history across multiple questions (each request can be treated independently unless a strong reason emerges during implementation to do otherwise).

## Further Notes

- Cost estimates discussed with the site owner before this spec was written (Claude Haiku via Bedrock, rough context + response sizing): roughly $0.02-0.05 for 10 prompts, $0.20-0.50 for 100 prompts, $2-5 for 1,000 prompts, with prompt caching bringing costs toward the lower end of each range. Lambda and DynamoDB costs at these volumes are effectively free under their respective free tiers/pay-per-request billing. These numbers assume Haiku and the token/size limits in this spec are actually enforced - they are not a substitute for the rate-limiting/circuit-breaker work itself.
- The site owner has a Claude Pro subscription, which was confirmed to be a separate product from API/Bedrock access (different quota, different billing, and Pro's consumer terms don't cover powering a public-facing service) - not a source of free/included usage for this feature.
