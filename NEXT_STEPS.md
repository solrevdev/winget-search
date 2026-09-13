# WinGet Search continuation plan

Updated: 2026-09-13. This is the current plan. The older tables in
`IMPROVEMENTS.md` retain historical notes and may describe completed work as open.
Use [NEXT_PROMPT.md](NEXT_PROMPT.md) to start the next review/implementation round.

## Project and constraints

- Repository: https://github.com/solrevdev/winget-search
- Live site: https://solrevdev.com/winget-search/
- Keep hosting free on GitHub Pages. Keep package extraction in GitHub Actions and
  search in the browser. No paid search service or required runtime backend.
- Source branch: `master`. The daily build publishes generated files to `gh-pages`.
  GitHub Pages must serve that branch's root. Never use `gh-pages` for feature work.
- Prefer small, tested PRs. Update this plan as each batch ships.

## Completed first batch

[PR #6](https://github.com/solrevdev/winget-search/pull/6) implements:

- Monikers from upstream manifests, including `vscode`; `vs code` expands to it.
- Ranking tiers: exact ID, exact moniker, exact name, prefix, then weaker matches.
- Default-locale metadata merged with nonempty English overrides; singleton support.
- Separate short descriptions and full descriptions.
- Compact cards with Copy visible and native Details for extra metadata.
- Correct result totals and a cap warning only above 200 matches.
- Nine Python tests and fourteen Node tests, with a PR test workflow.

Before this change, `vscode` and `vs code` omitted VS Code, standard `7-Zip` ranked
third below forks, and 254 of 14,837 records lacked names and publishers. The local
checks used the live catalog with ten records rebuilt from upstream manifests.
PR #6 is merged and deployed, and its feature branch is deleted. Live searches
passed verification. The 2026-09-13 review confirmed 14,837 deployed records,
matching `metadata.total`, with extraction timestamp `2026-09-13T17:49:13.386657`.

Earlier PR #3 already added regex-safe highlighting, ranking, paging, query URLs,
homepage/license links and publisher/tag actions. Do not rebuild these from scratch.

## Search batch: PR #7 merged and deployed

Released on 2026-09-13:

- [PR #7](https://github.com/solrevdev/winget-search/pull/7) is merged and closed.
  Merge commit: `ecd44500574a646ee5a030a8e524842049d54095`.
- [Build and Deploy](https://github.com/solrevdev/winget-search/actions/runs/34773992863)
  and [Pages publication](https://github.com/solrevdev/winget-search/actions/runs/34774194266)
  both passed. The merge's test workflow passed too.
- Public `search.js` and MiniSearch bytes match the merged source. The catalog has
  14,836 records, matching `metadata.total`, extracted at
  `2026-09-13T18:17:57.426295`.
- The saved browser suite passed on the public site at 1280px and 375px, including
  typo/ordinary ranking, filters, URL history, clipboard, Details, paging, and
  empty/error recovery, with no uncaught browser exceptions.
- Removed `codex/search-typos-filters` locally and remotely after comparing its tree
  with the deployed merge. Pruned remote references. Keep `master`, `gh-pages`, and
  the unresolved PR #5 branch. Master is clean and synced at handoff.
- All task-owned local servers and Playwright sessions are stopped; see the resource
  log below. The next bounded batch is PR #5 and issue #1, after scope agreement.

MiniSearch 7.2.0 now provides a locally served, lazy typo index for IDs, names, and
monikers. The existing scorer still handles ordinary searches. Fallback runs only
when no ordinary results satisfy the active filters. Punctuation in `C++`, `C#`,
`.NET`, and `Node.js` remains significant.

Publisher and tag clicks now add exact field constraints while preserving the text
query. Removable chips and `publisher=` / repeated `tag=` parameters retain state
across reload and browser history. One publisher and all selected tags must match.
The query can be empty when filters are active. Escape clears text, and Clear filters
removes constraints without clearing text.

Verified acceptance examples:

- `vscode`, `vs code` and `Visual Studio Code` retain the standard desktop package first.
- `visaul studio code` finds VS Code and `googel chrome` finds Google Chrome.
- `7-Zip` and `7zip` retain the standard package above forks.
- A publisher/tag filter excludes records outside that field, preserves the text
  query, and survives reload and back/forward navigation. Removing it restores results.
- Search remains responsive with the whole catalog at desktop and mobile widths.

## Approved scope and verification

The user reviewed and approved [PR #7](https://github.com/solrevdev/winget-search/pull/7),
merged on 2026-09-13 as `ecd44500574a646ee5a030a8e524842049d54095`. It includes
the search core, UI, local library and license, tests, asset-copy workflow changes,
and this roadmap. Hosting remains free on GitHub Pages, extraction stays in Actions,
and search stays in the browser. The catalog endpoint and existing `?q=` links remain.

- The pinned MiniSearch UMD build is 86,348 bytes, with its MIT license and source
  checksums in `vendor/`. It adds no build dependency or external search service.
  Fallback requires every term. Only alphabetic terms of four or more characters
  receive edit tolerance; terms of six or more characters allow two edits for
  transpositions such as `visaul`.
- Publisher and tag filters match whole values without case sensitivity. Text edits
  share a history entry within an edit session; filter actions create entries.
  Back/forward cancels pending input. Search stays disabled until data and the
  search library load, and failed assets show a recovery message.
- All 38 Node tests and nine Python tests pass, including the original 14 search
  regressions. New tests cover fallback, exact-field exclusion, combined filters,
  URL state, input timing, missing assets, and escaped chip labels.
- Browser checks pass against 14,837 live records at 1280px and 375px: ranking,
  punctuation, clipboard contents, Details, chips, reload, back/forward, filter-only
  URLs, keyboard shortcuts, paging, and empty/error states. Screenshots show no
  horizontal overflow. A separate 360px mobile emulation passed touch filter
  addition/removal and typo search. `tests/browser-search.js` retains the main checks.
- Chrome engine timings on this Mac: first typo search including lazy indexing
  took 62ms; warm queries took at most 30ms in the measured set. At 4× CPU slowdown,
  those figures were 237ms and 60ms. Engine creation took less than 1ms. These
  measurements exclude catalog download, rendering, and the 300ms input debounce;
  CPU throttling is a simulation, not a physical mobile-device benchmark.

SEO and deployment maintenance remain separate changes. The findings below define
their scope; this search batch does not implement them or close their issues.

### PR #5 and issue #1: SEO ready for review

[PR #5](https://github.com/solrevdev/winget-search/pull/5) remains on
`feat/seo-meta-sitemap-dataset`. Conflict repair `c5de9d1` merged master `35bed66`
and passed CI. The user approved the SEO scope on 2026-09-13. The implementation
is complete and awaiting review and merge approval. Nothing has deployed from
this batch; issues #1 and #4 remain open.

- `build_site.py` replaces shell stamps with a tested static build. One explicit
  HTTPS directory URL in `site_config.json` drives canonical/social metadata,
  Dataset download, sitemap, guide examples, and the generated 404 destination.
  Custom roots/subpaths and GitHub Pages user/project paths are covered. This
  completes the redirect portion of issue #4, subject to release verification.
- The build rejects empty/invalid catalogs and count mismatches. The preview used
  14,836 records and `2026-09-13T18:17:57.426295Z`, matching the live download.
  Dataset description and visible summary show the actual count; `dateModified`
  uses extraction time. `variableMeasured` uses `id`, not `packageId`.
- Removed Dataset `numberOfItems`, unsupported historical coverage/publication
  dates, and the repository-as-Dataset `sameAs` claim. John Smith matches the
  public owner profile; creator points to that profile. The MIT catalog license
  stays and does not describe individual software licenses.
- Sitemap dates use significant source/catalog changes, with no daily date stamp
  for an unchanged agent page. Unknown source dates are omitted. No `priority`,
  `changefreq`, or keywords meta tag is added. See [SEO.md](SEO.md) for primary
  guidance, public URL rules, and Search Console follow-up.
- Added header/main landmarks, skip links, package headings, hidden decorative
  SVGs, stronger text/button contrast, underlined footer links, wrapped install
  commands, and keyboard scrolling for guide code examples. The 1200 × 630 PNG
  was regenerated from its SVG after fixing overflowing caption text.
- All 38 Node regressions and all nine extraction tests pass, plus ten new Python
  build tests (19 Python total). Generated homepage, agent page, and 404 pass
  html-validate 11.15.0's HTML standard preset; JSON-LD/XML/PNG/SVG and workflow YAML
  checks pass. Search engine, extractor, vendor assets and catalog bytes remain
  unchanged. No required runtime service or app dependency was added.
- Saved search and SEO browser suites pass at 1280px and 375px with no uncaught
  exceptions. Checks cover ranking, URLs/history, filters, copy, Details, paging,
  empty/error recovery, landmarks, metadata, static count/freshness, keyboard
  navigation and overflow. Screenshots were inspected. Axe 4.13.0 reports zero
  violations in eight light/dark desktop/mobile page checks and four Copy
  hover/success checks after contrast and keyboard fixes. This is automated plus
  keyboard review, not a claim of full assistive-technology certification.

Keep this existing PR and branch. Start the later maintenance branch from synced
master after PR #5 merges, reuse the URL rule, and recheck mergeability at every
handoff. No separate competing SEO PR is needed. Future master edits can still
introduce conflicts.

After approval: merge, verify both Build and Deploy and Pages publication, then
verify live metadata/counts/dates, sitemap, preview image, redirect and search.
Only then remove the completed feature branch and sync master. Search Console
still requires an account check: confirm sitemap submission and indexing, inspect
both page URLs, and check the old creator/license validation status. Run Rich
Results Test against the deployed homepage. Keep issue #1 open until the required
live and account checks pass.

### Issue #4: deployment and documentation follow-up

- The footer link is fixed. README duplication, its missing `LICENSE` link target,
  placeholder site URL, and conflicting Pages setup claims remain.
- [Build 34772504747](https://github.com/solrevdev/winget-search/actions/runs/34772504747)
  restored a previous run's cache. Checkout reused the Git directory, detected the
  upstream default branch, and fetched updates. Older claims that every run clones
  afresh are incorrect. The unique run key still creates needless cache entries.
- Trial a versioned UTC daily key with prefix restore. Always run upstream
  checkout so both exact and prefix restores refresh. Remove the separate update
  step that assumes `origin/master`.
- PR #5 implements the shared URL rule and generated 404 destination, with
  project/user-site/custom-domain tests. Reuse that builder after PR #5 merges;
  do not reimplement or revert its redirect logic in the maintenance PR.
- Make `force_pages_update.sh` restore the starting branch on success and failure,
  reject dirty worktrees, use fast-forward-only updates, and stage only intended
  files. Test success and fetch/push failures with temporary local Git remotes.
  Handle a detached starting state explicitly before changing branches.

Baseline before this batch: 14 Node search tests and nine Python extraction tests
passed. PR #7 is now merged, deployed, and verified live as recorded above.

## Resource tracking and handoff

Record resources here as soon as they start. Include the owning task/batch, purpose,
process PID or tool session ID, port and URL, browser session name, temporary paths,
and status. Check the running process or session before stopping it; stale PIDs may
belong to another task. Keep unrelated services and browser sessions intact.

At every PR handoff, list resources that are still active and offer to tear them
down in one short question. Do not leave a server or browser unmentioned. If cleanup
is already authorized, do it and report the verified result. Update this log after
cleanup. Temporary files can remain as inert test evidence; distinguish them from
running resources.

| Resource | Owner and location | Status |
| --- | --- | --- |
| Playwright `winget-seo-pr5` | PR #5 parent; PID 66266; open exec session 51766; `http://127.0.0.1:8765/winget-search/`; screenshots/logs in `.playwright-cli/` | Passed and closed 2026-09-13; PID and session checked; search suite sessions 32055 and 89714 completed |
| SEO preview server, PID 66230 | PR #5 parent; exec session 12065; port 8765; `http://127.0.0.1:8765/winget-search/`; `/private/tmp/winget-seo-pr5-20260913/preview` | Stopped 2026-09-13; PID and port checked |
| SEO review files | PR #5 parent; `/private/tmp/winget-seo-pr5-20260913`; catalog, generated previews, isolated validation tools/npm cache and evidence; no port or browser yet | Inert files; live catalog has 14,836 records |
| Validation tool install | PR #5 parent; exec session 48988; `/private/tmp/winget-seo-pr5-20260913/tools` and `npm-cache`; no port/browser | Completed; axe-core 4.13.0 and html-validate 11.15.0 installed; no process remains |
| Preview server, PID 62533 | PR #7; port 8765; `http://127.0.0.1:8765/winget-search/`; `/private/tmp/winget-preview`; exec session 32615 | Stopped 2026-09-13; port checked |
| Staged preview server, PID 63164 | PR #7; port 8766; `http://127.0.0.1:8766/winget-search/`; `/private/tmp/winget-review-preview`; exec session 57935 | Stopped 2026-09-13; port checked |
| Playwright `winget-search` | PR #7 desktop/mobile-width checks | Closed 2026-09-13 |
| Playwright `winget-mobile` | PR #7 touch checks | Closed 2026-09-13 |
| Playwright `winget-release-check`, PID 63851 | PR #7 public deployment verification; `https://solrevdev.com/winget-search/`; no local server | Passed and closed 2026-09-13; PID checked |

Preview directories and `.playwright-cli/` screenshots/logs are inert evidence.
PR #5 also retains JSON test results and isolated validation tools under
`/private/tmp/winget-seo-pr5-20260913`. All PR #5 task resources are stopped;
no active browser, preview server or background test remains.
No task-owned servers or Playwright sessions remain active. Verified with
`playwright-cli list`, process checks, and listener checks on ports 8765 and 8766.
Unrelated services were left running.

PR #5 conflict repair (2026-09-13): no servers, browser sessions, background
processes, or temporary previews started. The read-only SEO scope subagent owns
review findings only and reports any resources to the parent. Its review is complete. Build and markup subagents started no servers or
browsers; their Python test fixture directories were cleaned automatically.

## Following batches

1. **Install-list builder.** Select multiple packages, keep selections in local
   storage, copy commands, and export a native WinGet import JSON file. Share lists
   through URLs if practical. No accounts or server storage. Offer silent/scripted
   options explicitly rather than silently accepting agreements by default.
2. **Smaller initial catalog and static detail pages.** The pre-change catalog was
   8.26 MB uncompressed. Generate a compact search index and fetch full descriptions
   and version history on demand. Generate package pages for direct links and SEO.
   Preserve the full `packages.json` endpoint and existing `?q=` links.
3. **Variant clarity.** Label Desktop, CLI and Insiders variants where reliable;
   consider grouping variants and separating strong matches from descriptive matches.
4. **Additional discovery.** Consider categories inferred from tags, installer type
   and architecture filters, command variants, and recent searches after the core
   search and selection flows work well. Installer filters require new extracted data.

## Agreed investigation and completion work

These are explicit roadmap tasks, alongside the search batches above. Investigate
each against current `master`, finish the remaining useful work, and record what
shipped or why an item no longer applies. Do not treat this list as a reason to
merge old code without review.

1. **Investigate and, if suitable, complete
   [PR #5](https://github.com/solrevdev/winget-search/pull/5).** Review the current
   diff, checks and merge conflicts after PR #6. Verify its Open Graph/Twitter tags,
   canonical URL, sitemap and Dataset fields against the deployed site and current
   data schema. Fix any remaining problems and validate the generated output before
   merging and deploying. Confirm live structured data has the actual package count
   and the sitemap has valid public URLs and dates. Check whether Search Console
   submission or validation still needs a separate follow-up. Keep its
   `feat/seo-meta-sitemap-dataset` branch until the PR is merged or otherwise resolved;
   clean it up only then.
2. **Investigate and complete
   [issue #4](https://github.com/solrevdev/winget-search/issues/4).** Reconcile every
   acceptance criterion with the current code. The footer link is already fixed.
   Address remaining README duplication and license filename mismatch, cache/update
   logic, default-branch detection, generated redirect paths, and restoring the
   original branch in `force_pages_update.sh`. Cache restore keys exist; inspect
   actual reuse and checkout conditions rather than assuming every restore misses.
   Verify workflow and helper-script behavior, preserve Pages deployment, and close
   the issue only when the remaining criteria are met or explicitly resolved.
3. **Investigate and complete
   [issue #1](https://github.com/solrevdev/winget-search/issues/1).** Coordinate with
   PR #5 to avoid duplicate SEO work. Check the title, description, semantic elements,
   heading order, image alt text and social metadata against the live page. Assess
   the issue's older suggestions against current search-engine guidance. Complete
   useful gaps and record any suggestions that no longer apply. Verify the deployed
   result before closing the issue; merging PR #5 alone does not prove the whole
   issue is complete.

## Other maintenance work

- `IMPROVEMENTS.md` #24: non-PEP440 versions currently fall back to `0.0.0`. This can
  choose the wrong latest version. Fix with representative upstream version tests.
- Keep timestamps and catalog health visible; consider failing a build on a major
  unexplained drop in package count or required metadata.
- Older low-priority housekeeping remains in `IMPROVEMENTS.md`, including template
  configuration files, license placeholders, and generated-data policy.

## Prior art and references

| Reference | What to study |
|---|---|
| https://github.com/tulior/wingetdb | Closest static/GitHub Pages design: package pages, index, version history |
| https://winstall.app/express | Familiar app selection and new-machine setup |
| https://wingetly.io/docs | Field filters, browser-stored packs, shareable links |
| https://winget.run/ | Compact discovery and selection; its API repository is archived |
| https://github.com/Devolutions/UniGetUI | Desktop package bundles and install options |
| https://lucaong.github.io/minisearch/ | Browser search with field weights, prefixes and fuzzy matching |
| https://learn.microsoft.com/en-us/windows/package-manager/winget/import | Native package-list JSON format |

Borrow useful interaction ideas, not hosting dependencies. Verify freshness when
comparing catalogs; the alternatives do not all update reliably.

## Development and verification

```sh
uv run --no-project --with pyyaml --with packaging python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
git diff --check
```

The local `.venv` also has the Python dependencies. `packages.json` is a tracked
empty placeholder despite its ignore entry. Use a temporary preview directory with
the site assets and a downloaded current catalog for browser testing. Do not commit
the downloaded catalog. Temporary files from previous sessions are not required.

Start a local static server for that preview, then run:

```sh
playwright-cli --help
playwright-cli -s=winget-search open http://127.0.0.1:8765/winget-search/ --browser chrome
playwright-cli -s=winget-search run-code --filename tests/browser-search.js
```

The script uses the opened page's base URL, checks desktop/mobile widths, and saves
screenshots under `.playwright-cli/`. For a preview served at another path or port,
open that URL instead.

Use the browser order in the user's global instructions. `playwright-cli` is
available; read its help. In Codex it may need sandbox escalation for browser cache
files. Check desktop/mobile layout, clipboard contents, Details, paging, query URLs,
keyboard interaction, and empty/error states when affected.

After an approved merge, wait for both Build and Deploy and Pages publication, then
check live HTML, fresh catalog metadata and representative searches. A successful
build alone does not prove the public site updated. Remove only the completed
feature branch locally and remotely, prune remote-tracking refs, and return to a
clean `master` that matches `origin/master`.
