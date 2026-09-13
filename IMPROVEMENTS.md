# Remaining improvements

Use [NEXT_STEPS.md](NEXT_STEPS.md) for the next batch, release evidence and resources.
This is the later backlog. Numbers below retain the original item IDs, not GitHub
issue numbers. Check current code before choosing work.

## Maintenance

Issue #4's README, cache and Pages helper work is implemented and awaiting PR
review/release. See [NEXT_STEPS.md](NEXT_STEPS.md) for checks and remaining release
steps. The shared public URL and 404 destination shipped in PR #5; see
[SEO.md](SEO.md) before changing either.

| ID | Remaining work | Files / constraint |
|---|---|---|
| #17 | Trim unused .NET/template settings where safe. | `.editorconfig`, `omnisharp.json`, `.dockerignore`; retain useful editor rules. |
| #18 | Replace the license holder placeholder with the confirmed holder. | `license.txt`. |
| #25 | Set one catalog tracking policy. The file is tracked despite its ignore rule and README's claim that it is not in source. | `packages.json`, `.gitignore`, `README.md`; preserve the public endpoint. |

## Later features and extraction

| ID | Candidate | Decision needed |
|---|---|---|
| #13 | Offer copy-command variants. | Keep the default command simple; only add options with a clear use. |
| #15 | Reduce initial catalog/search work with generated assets. | Measure load/search cost first; consider a smaller initial catalog and static package detail pages while keeping `packages.json`. |
| #16 | Infer package categories from tags. | Prove that the mapping helps beyond current tag filters. |
| #24 | Compare non-PEP440 versions without collapsing them all to `0.0.0`. | Define deterministic ordering from real manifests and add fixtures before changing latest-version selection. |
| New | Export a selected install list. | Agree the selection, export format and command behavior in a bounded feature batch. |

## Completed reference

Regex-safe highlighting, compact JSON, ranking, descriptions, paging, query URLs,
links, filters, package details, typo tolerance, locale docs, dead-code cleanup and
the shared 404 URL are complete (#1, #3, #5–#12, #14, #19, #23, #26).
Implementation and older review detail live in Git history and
[PR #3](https://github.com/solrevdev/winget-search/pull/3),
[PR #6](https://github.com/solrevdev/winget-search/pull/6),
[PR #7](https://github.com/solrevdev/winget-search/pull/7) and
[PR #5](https://github.com/solrevdev/winget-search/pull/5).

Keep completed detail there. Replace resolved backlog rows instead of appending
new status tables or session transcripts.
