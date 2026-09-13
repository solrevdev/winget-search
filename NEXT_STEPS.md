# WinGet Search: status and next work

Updated: 2026-09-13. Read this first; use `NEXT_PROMPT.md` to resume.
Keep this file short: replace current status, link release evidence, and move only
unresolved work forward. Git history and PRs retain detailed past investigations.

## Constraints and current state

- Source: `master`; generated deployment: `gh-pages`. Never develop on `gh-pages`.
- Free GitHub Pages hosting, extraction in Actions, search in the browser.
- Preserve `packages.json`, query/filter URLs, ranking, copy and Details behavior.
- `site_config.json` holds the public URL; reuse `build_site.py` for metadata,
  guides, sitemap and redirect. See `SEO.md` for that contract and source guidance.
- Live site: https://solrevdev.com/winget-search/
- PR #5 merged at `1d87f32`, deployed and verified live; its branch is cleaned up.
- Issue #4 maintenance is on `codex/issue-4-maintenance`, based on synced `master`
  at `a22dc4d`. Implementation is tested in
  [PR #8](https://github.com/solrevdev/winget-search/pull/8); review and release are next.

## Completed

| Release | Result and evidence |
| --- | --- |
| [PR #3](https://github.com/solrevdev/winget-search/pull/3) | Safe highlighting, ranking, paging, query URLs and package links. |
| [PR #6](https://github.com/solrevdev/winget-search/pull/6) | Monikers/aliases, locale merging, compact cards and correct counts; deployed and verified. |
| [PR #7](https://github.com/solrevdev/winget-search/pull/7) | Lazy typo fallback and exact publisher/tag filters; [build](https://github.com/solrevdev/winget-search/actions/runs/34773992863) and [Pages](https://github.com/solrevdev/winget-search/actions/runs/34774194266) passed; live desktop/mobile checks passed. |
| [PR #5](https://github.com/solrevdev/winget-search/pull/5) | Canonical/social metadata, accurate Dataset/count/dates, shared public URLs, sitemap, preview image and accessibility. [Build](https://github.com/solrevdev/winget-search/actions/runs/34775515056) and [Pages](https://github.com/solrevdev/winget-search/actions/runs/34775751604) passed; live desktop/mobile SEO and search checks passed. |

PR #5 live evidence: 14,836 records, matching count and Dataset freshness
`2026-09-13T18:48:13.094889Z`. All 12 checked assets match the expected build;
unknown paths return the generated HTTP 404. No uncaught browser exceptions.

Issue #1 closed with PR #5. Its title/description, social metadata, semantics,
headings and image requirements are implemented; Google ignores its proposed
keywords meta tag. Search Console account work remains separate below.
PR #5 also addresses issue #4's redirect; issue #4 is only partly complete.

## Issue #4 maintenance: PR #8 awaits review

The agreed batch is implemented in
[PR #8](https://github.com/solrevdev/winget-search/pull/8). Check its latest CI result
before merging; merge approval is still required:

- README duplication, license link, live URL and Pages claims corrected; stale
  search/development guidance trimmed.
- Versioned UTC daily cache key with prefix restore. Unconditional upstream
  checkout refreshes exact hits too and resolves the current default branch.
- Pages helper rejects dirty/detached starts, uses a temporary worktree and
  fast-forward updates, and commits only intended files. The starting branch and
  HEAD stay unchanged. Failed work is retained with its path for inspection.
- Existing public URL/build rules, search behavior and catalog format preserved.

Local validation: all **38 Node and 34 Python tests** pass (the original 19 Python
checks plus 15 maintenance checks). Checkout smoke tests exercise the unmodified
v4 action against local Git remotes and a stub API: miss, exact hit, prefix restore,
renamed default branch, Git directory reuse and credential removal all pass.
The smoke test also runs in PR CI. ShellCheck, Bash syntax and diff checks pass.

Both browser suites pass at 1280px and 375px; Chrome query URLs and the footer pass.
All 13 built files match PR #5's expected build byte for byte with its saved
14,836-record catalog. Inline JavaScript, JSON-LD, sitemap and README links pass.

Wait for merge approval. After merge, check both deployment stages and the live
site before closing [issue #4](https://github.com/solrevdev/winget-search/issues/4)
or cleaning up the branch. Confirm the first v2 cache save and a later exact hit
in Actions logs; local smoke tests do not prove hosted cache transfer.

## Later work

- Install-list builder: browser storage, multi-package selection, copy/export to
  native WinGet import JSON; optional shared URLs. No accounts or backend.
- Smaller initial index and static package detail pages; retain full catalog API.
- Clear Desktop/CLI/Insiders variants, then categories and installer filters where
  extracted data supports them.
- `IMPROVEMENTS.md` holds the small remaining technical backlog, including version
  ordering and template cleanup. Do not treat old resolved suggestions as open.

## Account follow-up

Search Console needs the owner's account: confirm sitemap submission and page
indexing, inspect both page URLs, and check historical Dataset creator/license
validation. Run Rich Results Test against the deployed homepage. No current
account result has been verified. This is separate from issue #1's shipped HTML
requirements and is not a ranking guarantee.

## Checks and release procedure

Baseline: **38 Node and 34 Python tests** (nine extraction, ten build, 15 maintenance),
plus the checkout cache smoke test in CI.

```sh
node --test tests/*.test.cjs
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

Use an isolated Python environment if `.venv` is absent. Keep downloaded catalogs
and previews outside the checkout; tracked `packages.json` is an empty placeholder.
Build with `python build_site.py --packages /path/to/catalog --output-dir /path/to/preview`.
Read `playwright-cli --help`; run `tests/browser-search.js` and `tests/browser-seo.js`
on affected desktop/mobile flows. Validate generated HTML, JSON-LD, XML and images.

Wait for merge approval. After merge, verify Build and Deploy **and** Pages
publication, then the live assets and browser flows. Delete only verified completed
branches, prune remote refs and leave clean synced master. Docs-only handoff commits
may use `[skip ci]` after confirming they change no deployed inputs.

## Resource log

Record owner, purpose, PID/session, URL/port, paths and status as resources start.
Stop only verified task-owned resources; retain only current status here.

- Parent-owned preview: Python PID `70712`, session `29537`, port `8765`,
  `http://127.0.0.1:8765/winget-search/`. Stopped after browser checks.
- Parent-owned Playwright `winget-issue4`: daemon PID `71569`, open session `96019`,
  search `39278`, SEO `63409`, final checks/close `54198`. Closed after checks.
- Checkout smoke PID `70739`, API port `62464`, session `77790`: passed and stopped;
  temporary Git fixtures removed. Unit-test remotes/worktrees removed on exit.
- Evidence: `/private/tmp/winget-issue4-20260913` (preview, action source and checks)
  and `.playwright-cli/` (screenshots/logs). Inert files only; no task-owned servers
  or browsers remain. Prior release evidence remains at
  `/private/tmp/winget-seo-pr5-20260913/live`. Unrelated resources left intact.
