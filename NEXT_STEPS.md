# WinGet Search continuation plan

Updated: 2026-09-13. This is the current plan. The older tables in
`IMPROVEMENTS.md` retain historical notes and may describe completed work as open.

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

## Search batch: implemented, awaiting PR review

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

The user approved a search-only batch on `codex/search-typos-filters`. It includes
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

### PR #5 and issue #1: one SEO change

[PR #5](https://github.com/solrevdev/winget-search/pull/5) remains open and mergeable
at `949eec26e58f8f392d505a4cabba752264d3da94`, with no reported checks. Preserve
`feat/seo-meta-sitemap-dataset` and complete the useful issue #1 work there.

- Canonical and social metadata are absent from the live homepage. PR #5 supplies
  these, including a PNG preview and its SVG source. Its description is stale:
  it still lists the image as future work despite including it in the diff.
- The count stamp reads the correct `metadata.total` field. Validate it against
  the actual array length. Change `variableMeasured` from `packageId` to `id`.
  Review the count representation: Schema.org defines `numberOfItems` for
  [ItemList](https://schema.org/numberOfItems), not Dataset.
- Use catalog freshness for Dataset dates and meaningful page-change dates for
  sitemap entries. Do not stamp an unchanged agent-access page with every build's
  date. [Google's sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
  calls for accurate last-modified dates and ignores priority/change frequency.
- The homepage already has a title, description, h1, and footer. Add useful
  header/main landmarks, result headings, and appropriate treatment of decorative
  SVGs. This search batch adds an explicit search label. Keep the PNG's social alt descriptions. Do not add
  the issue's keyword meta tag: [Google ignores it](https://developers.google.com/search/docs/crawling-indexing/special-tags).
- Share a single public-base-URL rule with issue #4's generated redirect. Validate
  project paths and custom-domain paths together with canonical and sitemap URLs.
- Validate generated HTML, JSON-LD, sitemap, and preview assets before review.
  After an approved merge, verify both deployment stages and the live output.
  Search Console submission and the old validation status still need a separate
  account check. Keep issue #1 open until its remaining criteria are resolved and
  the deployed result is verified.

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
- Generate the 404 destination using the public URL rule established with PR #5.
  Test project paths, user-site roots, and custom domains.
- Make `force_pages_update.sh` restore the starting branch on success and failure,
  reject dirty worktrees, use fast-forward-only updates, and stage only intended
  files. Test success and fetch/push failures with temporary local Git remotes.
  Handle a detached starting state explicitly before changing branches.

Baseline before this batch: 14 Node search tests and nine Python extraction tests
passed. The current search branch awaits review and has not been merged or deployed.

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
