# 01: Rename GitHub repo to `griz` and fix default branch

**What to build:** `Ditmanson/freeOpenSourceIGP` becomes `Ditmanson/griz` on GitHub, `main` (the branch with all real history and the one Amplify actually deploys) becomes the GitHub-designated default branch instead of the stub `master`, and the local checkout is renamed and repointed so `git fetch`/`git push` keep working against the new URL.

**Blocked by:** None (can start immediately).

**Status:** done

- [x] `gh repo view Ditmanson/griz` shows the repo (renamed, not a new repo)
- [x] Repo's default branch is `main`
- [x] Local `origin` remote points at `github.com:Ditmanson/griz.git` and `git fetch`/`git push` succeed
- [x] Local working directory moved from `/home/travis/repos/freeOpenSourceIGP` to `/home/travis/repos/griz`
- [x] `master` branch (the unrelated 1-commit stub) is left alone — not deleted, not touched, just no longer default
