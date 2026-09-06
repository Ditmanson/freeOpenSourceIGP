# Deploying this site

Hosted on AWS Amplify (app `griz`, `d21bji1dm3np6x`), which redeploys automatically on push to `main`.

**Amplify's build step for this app does not run `hugo build`.** Its buildSpec has an empty build command and just publishes whatever is already committed in `public/` as-is. This means any change to `content/`, `layouts/`, or `hugo.yaml` will NOT show up live from a push alone — `public/` has to be manually rebuilt and committed first:

```
rm -rf public/* && hugo && git add public && git commit && git push
```

Forgetting this step is silent: the push succeeds, Amplify reports a successful build, but the live site keeps serving the old `public/` HTML. If a change doesn't seem to be taking effect after a deploy, check whether `public/` was actually rebuilt for that commit.
