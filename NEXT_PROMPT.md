Continue work in /Users/solrevdev/Projects/winget-search.
Read NEXT_STEPS.md and IMPROVEMENTS.md. Verify GitHub and local Git state before
acting; release notes describe past checks, not current status.

Review the remaining nonstandard version-ordering risk in extract_packages.py.
Find real manifest examples that fall back to 0.0.0, explain the selection risk,
and propose a bounded deterministic fix with focused tests. Wait for agreement
before implementing. Preserve valid-version ordering and the catalog format.

Use a fresh branch from synced master. Reuse site_config.json and build_site.py;
preserve search, query/filter URLs, ranking, copy and Details. Keep all existing
regression tests and the checkout cache smoke test. Keep docs lean and track
resources as they start.

Leave a tested PR for review. Wait for merge approval, then verify Build and
Deploy, Pages publication and the live site before cleaning up completed branches
and task-owned resources. Keep unrelated backlog and account work separate.
