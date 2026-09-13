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
Production must rebuild the whole catalog during deployment. Check PR #6 and its
deployment runs for the final merge and release state.

Earlier PR #3 already added regex-safe highlighting, ranking, paging, query URLs,
homepage/license links and publisher/tag actions. Do not rebuild these from scratch.

## Next batch: typo tolerance and true filters

Trial a self-hosted browser search library such as MiniSearch against the current
scorer. Add fuzzy matching as a fallback and keep exact IDs, monikers and names first.
Preserve meaningful punctuation in `C++`, `C#`, `.NET` and `Node.js`.

Turn publisher and tag clicks into actual constraints that preserve the text query.
Use removable filter chips and shareable query parameters. Today these clicks just
replace the text query with another broad search.

Acceptance examples:

- `vscode`, `vs code` and `Visual Studio Code` retain the standard desktop package first.
- `visaul studio code` finds VS Code and `googel chrome` finds Google Chrome.
- `7-Zip` and `7zip` retain the standard package above forks.
- A publisher/tag filter excludes records outside that field, preserves the text
  query, and survives reload and back/forward navigation. Removing it restores results.
- Search remains responsive with the whole catalog at desktop and mobile widths.

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
node --test tests/search.test.cjs
git diff --check
```

The local `.venv` also has the Python dependencies. `packages.json` is ignored and
may be an empty local placeholder. Fetch a current catalog or regenerate it before
browser testing. Temporary preview files from a previous session are not required.

Use the browser order in the user's global instructions. `playwright-cli` is
available; read its help. In Codex it may need sandbox escalation for browser cache
files. Check desktop/mobile layout, clipboard contents, Details, paging, query URLs,
keyboard interaction, and empty/error states when affected.

After an approved merge, wait for both Build and Deploy and Pages publication, then
check live HTML, fresh catalog metadata and representative searches. A successful
build alone does not prove the public site updated. Remove only the completed
feature branch locally and remotely, prune remote-tracking refs, and return to a
clean `master` that matches `origin/master`.
