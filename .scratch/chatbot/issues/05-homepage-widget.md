# 05: Homepage widget

**What to build:** A real visitor can actually use the chatbot on the homepage - a htmx+Alpine chat widget, consistent with the comments feature's UI approach, calling the Lambda Function URL directly from the browser.

**Blocked by:** 03 (wants the Lambda actually answering meaningfully, grounded in real content, before building UI around it)

**Status:** ready-for-agent

- [ ] A chat widget (question input, submit, answer display, loading/error/rate-limited states) is added to `layouts/home.html` only - no other template renders it
- [ ] `layouts/_partials/head.html`'s existing `{{ if eq .Kind "page" }}` guard (which loads htmx/Alpine/Mustache) is extended, or paralleled, to also cover `Kind == "home"`, since the widget reuses the same htmx/Alpine stack already established for comments
- [ ] The widget calls the Lambda Function URL directly via htmx, with Alpine driving UI state (loading, answer display, error, rate-limited) - consistent with the pattern established for comment posting
- [ ] A rate-limited response (from ticket 02's enforcement) is shown to the visitor clearly, not as a generic/broken error
- [ ] Verified in a real browser against the live Lambda: asking a real question on the homepage produces a real, grounded answer in the UI; visiting any non-homepage page confirms the widget is absent
- [ ] No AWS/Lambda changes - this ticket is client-side only
- [ ] No changes to `public/` until the final ticket rebuilds it
