# 02: Repoint AWS Amplify at the renamed repo and update docs

**What to build:** Amplify app `d21bji1dm3np6x` is renamed from `freeOpenSourceIGP` to `griz` and its stored `repository` field/webhook keep tracking the GitHub repo under its new name (`Ditmanson/griz`), verified by an actual push-to-`main` that triggers a build and lands on the live site at griz.sh. `docs/deploys.md` is updated to stop calling the app `freeOpenSourceIGP`.

**Blocked by:** 01 (the GitHub repo must already be renamed to `griz` before Amplify can be repointed at it).

**Status:** done

- [x] `aws amplify get-app --app-id d21bji1dm3np6x` shows `name: griz`
- [x] Amplify's `repository` field (and the underlying webhook/deploy key) references `Ditmanson/griz`, not the old URL — succeeded via `aws amplify update-app --oauth-token $(gh auth token)`, no console step needed
- [x] A real push to `main` (commit `d7dd3ed`) triggered Amplify job 38, which succeeded
- [x] `docs/deploys.md` refers to the app as `griz`, not `freeOpenSourceIGP`
