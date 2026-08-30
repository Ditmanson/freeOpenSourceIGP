# 06: Final live verification, push, and tag

**What to build:** The full chatbot feature verified end-to-end on the live, deployed site, including deliberately exercising the safety limits, before tagging a release.

**Blocked by:** 04, 05

**Status:** ready-for-agent

- [ ] `public/` is rebuilt and committed per `docs/deploys.md`, and the Amplify deploy is confirmed to succeed
- [ ] On the live site: a real question on the homepage gets a real, grounded answer; the widget is absent from every other page
- [ ] A deliberate rate-limit test against the live Function URL confirms the visitor-facing rejection message and (if feasible without materially affecting real spend tracking) confirms the CloudWatch alarm/notification path fires
- [ ] Confirmed that email/calendar tools remain disabled by default on the live deployment, and that the capability config file is the actual, sufficient mechanism to change that later (no additional undocumented steps required)
- [ ] This is the point at which the site owner decides whether to tag a new release
