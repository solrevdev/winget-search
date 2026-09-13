Continue work in /Users/solrevdev/Projects/winget-search.
Read NEXT_STEPS.md first, then this file. Use SEO.md for the public URL contract.

The agreed issue #4 maintenance batch is implemented on
codex/issue-4-maintenance from synced master at a22dc4d. It cleans the README,
uses a UTC daily cache key and unconditional upstream checkout, and isolates the
Pages helper in a temporary worktree so the starting branch stays unchanged.
Dirty/detached starts are rejected; failed work is retained for inspection.

Check the PR and its CI results. Leave it ready for review and wait for explicit
merge approval. Do not treat implementation agreement as merge approval.
After approval, merge and verify Build and Deploy, separate Pages publication,
and the live assets and desktop/mobile browser flows. Confirm the v2 cache save
and a later exact hit in Actions logs. Close issue #4 only after release checks
pass, then clean up the completed branch and leave master clean and synced.

Keep the public URL/build rules in site_config.json and build_site.py. Preserve
packages.json, query/filter URLs, ranking, copy and Details. Retain all 38 Node
and 34 Python tests plus the actual checkout cache smoke test in CI. The original
19 Python tests remain; the 15 new tests cover workflow/helper behavior. No search
or SEO changes belong in this batch.

Keep docs lean and record resources as they start. Local browser/server checks
are complete and task-owned processes are stopped; evidence paths are in
NEXT_STEPS.md. Preserve unrelated resources. The later feature backlog and
Search Console account work remain separate. Propose the next batch only after
this release is complete.
