# Remaining work

This is the single backlog. [README.md](README.md#work-across-sessions) holds the
working rules; [NEXT_PROMPT.md](NEXT_PROMPT.md) holds the task handoff and resources.
Check the code and GitHub before choosing work. These are proposals, not approved
implementation scope. The tracked empty catalog placeholder is documented in the
README; that policy is settled.

## Maintenance

| Work | Remaining decision |
| --- | --- |
| Refresh Actions runtime support | Address the Node-runtime warning recorded in PR #8 release runs; check supported action versions and rerun checkout smoke tests. |
| Remove unused template settings | Review `.editorconfig`, `omnisharp.json`, `.dockerignore` and redundant ignores; retain useful editor rules. |
| Replace the license holder placeholder | Confirm the copyright holder before changing `license.txt`. |

## Product and performance

| Candidate | Scope to agree |
| --- | --- |
| Install-list builder | Browser storage, package selection and native WinGet import JSON export; optional shared URLs, no backend. |
| Smaller initial index and static package pages | Measure load cost first; retain the full catalog API. |
| Clear Desktop/CLI/Insiders variants | Distinguish related packages without weakening exact-ID ranking. |
| Categories and installer filters | Prove which manifest fields support useful, accurate filters. |
| Copy-command variants | Add only commands with a clear use; preserve the current default. |

## Owner account follow-up

Confirm Search Console sitemap submission and indexing, inspect both public pages,
review historical Dataset validation and run Rich Results Test. Record the date
and outcome. See [SEO.md](SEO.md); shipped metadata work is complete.
