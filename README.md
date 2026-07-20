# Origin
> **AI disclosure:** Parts of this project (code, tests, CI/CD automation and
> documentation) were created or assisted by AI tools. All changes are gated by
> automated tests and a human is expected to review anything that fails.

Imagine you have a self hosted server at your home and the public ip is changing occasionally. You want to use your own domain to host some services and have your dns setup in aws route53.

# What route53-dyndns does
- fetch public ip of the current machine (where the script is executed)
- set multiple route53 records matching by name to this public ip if it is different
- repeating every 5min.


## docker-compose example:
```
version: '3'

services:
  awsdomain:
  image: tomfankhaenel/route53-dyndns:1.0.0
  restart: always
  environment:
    - ROUTE53_ZONE=$ZONEID
    - ROUTE53_RECORDS=record.,*.record2.
    - AWS_ACCESS_KEY_ID=$KEY
    - AWS_SECRET_ACCESS_KEY=$SECRET
```

# Automation

This repository is fully automated:

- **Dependency updates** are opened by Renovate as Conventional-Commit pull requests.
- **CI** (`.github/workflows/ci.yml`) runs the functional test suite (`src/test_main.py`) and a multi-arch Docker build on every PR.
- **Auto-merge**: Renovate merges an update only when *all* CI checks are green. If a test breaks, the PR is left open and labelled for a human to review — it is never merged.
- **Daily release** (`.github/workflows/release.yml`): once a day, if anything was merged since the last tag, a new release is created. The version is bumped major/minor/patch based on the merged commit messages, which then builds and pushes the image.

Required repository secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
