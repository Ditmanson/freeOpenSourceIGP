# 03: Site content index and real capabilities (search + video links)

**What to build:** The chatbot becomes genuinely useful and grounded in real site content, gated behind the safety net from ticket 02. Adds a Hugo build-time content index, a single capability config file defining the chatbot's tools, and wires both into the Lambda along with prompt caching for the repeated context.

**Blocked by:** 01, 02 (the rate-limit/spend safety net must exist before the Lambda does anything more expensive or capable)

**Status:** ready-for-agent

- [ ] Hugo generates a JSON content index at build time (a custom output format, the same mechanism used for client-side search widgets) containing at minimum each page's title, URL, tags, and a short summary/excerpt - kept current automatically as content changes, no manual maintenance
- [ ] A single capability config file (bundled with the Lambda deployment) defines the chatbot's available tools as a list with at least a name, description, and enabled flag - at minimum `search_site_content` and `list_videos`, both enabled
- [ ] The same config file also defines `send_email` and `check_calendar` (or similarly named) entries, explicitly `enabled: false` - establishing the shape for later expansion without a handler-code redesign
- [ ] The Lambda's handler logic reads this config file and only offers *enabled* tools to the model via Claude's tool-use mechanism - disabling a tool in the file is sufficient on its own to make the model unable to use it, with no other code changes required
- [ ] The site-content-index context is sent using Bedrock/Claude's prompt caching mechanism, since it's identical across requests within its cache window
- [ ] Verified via direct `curl` calls to the Function URL: a question referencing real site content (e.g. asking about a specific dog training topic or for video recommendations) gets an answer that's genuinely grounded in and references real posts/videos from the site, not generic/hallucinated content
- [ ] Verified that disabling a tool in the config file (temporarily, for the test) and redeploying actually removes the model's ability to use it, confirming the "single file" control claim is real, not aspirational
- [ ] No changes to `public/` in this ticket (the Hugo output-format change affects the build, but the homepage widget that surfaces this isn't built until ticket 05, and `public/` isn't rebuilt/pushed until ticket 06)
