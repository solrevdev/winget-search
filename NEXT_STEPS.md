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
- PR #5 merged at `1d87f32`, deployed and verified live. Its feature branch was
  removed locally/remotely; refs pruned. Master is clean and synced at handoff.

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

## Next bounded batch: remaining issue #4 maintenance

Propose scope and wait for agreement before implementing from synced `master`.

1. Fix README duplication, license link, placeholder URL and Pages setup claims.
2. Use a versioned UTC daily cache key with prefix restore. Always refresh the
   upstream checkout, including exact cache hits; remove the separate step that
   assumes `origin/master`. Prefix restoration already works; do not claim it is
   absent. Verify actual reuse and default-branch behavior.
3. Make `force_pages_update.sh` reject dirty worktrees, use fast-forward updates,
   stage only intended files and restore its starting branch on success/failure.
   Handle detached HEAD explicitly. Test with temporary local Git remotes.
4. Reuse PR #5's URL/build rules. Footer and redirect are done; do not rebuild them.

Keep this batch separate from new search features. Close
[issue #4](https://github.com/solrevdev/winget-search/issues/4) only after its
remaining criteria and release checks pass.

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

Baseline: **38 Node tests and 19 Python tests** (nine extraction, ten build).

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

Record resources immediately: owner, purpose, PID/tool session, browser name,
port/URL, paths and status. Stop only verified task-owned resources. At handoff,
list anything active; offer cleanup unless already authorized. Keep only the
current resource summary here; old process details remain in Git history.

- PR #5 release: Build `34775515056`, Tests `34775515024`, Pages `34775751604`
  passed. Both live browser suites passed at 1280px and 375px.
- Playwright `winget-seo-release`: parent-owned live checks at
  `https://solrevdev.com/winget-search/`; PID 67800, open session 56658, test
  session 75443. Closed; PID/session checked. No local server was started.
- No task-owned browsers or servers remain. Ports 8765/8766 checked; prior preview
  resources remain stopped. Unrelated resources were left intact.
- Evidence: `/private/tmp/winget-seo-pr5-20260913/live` and `.playwright-cli/`;
  inert test results, screenshots and downloaded files. Prior tools/previews in
  the parent directory are inert too. Old resource details remain in Git history.
