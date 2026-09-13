# Work and release guide

Use [IMPROVEMENTS.md](IMPROVEMENTS.md) as the single backlog and
[NEXT_PROMPT.md](NEXT_PROMPT.md) to start the next task. Check local Git and GitHub
before acting; the release evidence below records past checks, not current status.

## Project contracts

- Source work targets `master`; `gh-pages` contains generated deployment files.
- Keep hosting free on GitHub Pages, extraction in Actions and search in the browser.
- Preserve the public catalog format, query/filter URLs, ranking, copy and Details.
- Reuse `site_config.json` and `build_site.py` for public URLs and generated assets.
  See [SEO.md](SEO.md); changing the URL does not configure DNS or Pages.
- Keep the tracked `packages.json` as an empty source placeholder. Put downloaded
  catalogs and previews outside the checkout. See [README.md](README.md) for setup.

## Verified release: 2026-09-13

[PR #8](https://github.com/solrevdev/winget-search/pull/8) completed the README,
cache and Pages-helper maintenance. [Issue #4](https://github.com/solrevdev/winget-search/issues/4#issuecomment-5655529591) records the
build, Pages, cache and live-site evidence supporting its closure.

Recorded validation: 38 Node and 34 Python tests, checkout reuse smoke tests,
ShellCheck, and desktop/mobile browser suites passed. Both builds and Pages
publications passed. The repeat build restored the exact daily cache key and
still fetched upstream. All 13 live files matched the expected build; unknown
paths returned the generated HTTP 404.

## Working checks

Create a fresh branch from synced source after agreeing scope. Use an isolated
Python environment and run:

```sh
node --test tests/*.test.cjs
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

CI also runs `tests/checkout-cache-smoke.py` against the checkout action bundle.
For affected site flows, build a preview with `build_site.py` and run
`tests/browser-search.js` and `tests/browser-seo.js` at desktop and mobile widths.
Read `playwright-cli --help` before use.

Leave a tested PR for review and wait for merge approval. After merging, verify
Build and Deploy, separate Pages publication and the live site before closing
issues or deleting completed branches. Docs-only handoff commits may use
`[skip ci]` after checking that no deployed inputs changed.

## Resources

Record owner, purpose, PID/session, URL/port, paths and status when resources start.
Stop only task-owned resources; leave unrelated processes and files intact.

Cleanup checked on 2026-09-13: release browsers were closed; task previews, downloads,
local test environments and Python caches were moved to Trash. The completed
feature branch was removed locally and remotely, refs pruned, and source synced. Recheck these
facts before the next task. Durable release evidence lives in issue #4 above.
