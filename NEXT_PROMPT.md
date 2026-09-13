Continue work in /Users/solrevdev/Projects/winget-search.
Read NEXT_STEPS.md first. It holds current status, release evidence and resources.
Use SEO.md for the public URL contract and IMPROVEMENTS.md for later backlog.

PRs #5, #6 and #7 are merged, deployed and verified. Master is clean and synced;
completed feature branches and task-owned servers/browsers are cleaned up.
Propose one bounded batch for the remaining issue #4 work and wait for agreement:
README duplication/license/URL/Pages claims; reusable upstream cache with reliable
refresh/default-branch handling; and safe starting-branch restoration in
force_pages_update.sh, including dirty/detached states and failure tests.
The footer and shared public URL/404 logic are done. Reuse build_site.py and
site_config.json. Start a fresh branch from synced master; do not reopen SEO work.

Keep hosting free on GitHub Pages, extraction in Actions and search in the browser.
Preserve packages.json, query/filter URLs, ranking, copy and Details. Retain all
38 Node and 19 Python tests, add focused workflow/helper tests, and check affected
browser flows. Use subagents when useful with clear ownership and resource reports.

Keep docs lean: replace resolved status, retain a short done/next/backlog log, and
link PRs for detail. Record resources as soon as they start. At handoff, tear down
verified task-owned resources when authorized and preserve unrelated ones.

Leave the PR tested and ready for review. Wait for merge approval, then verify
Build and Deploy, Pages publication and the live site before branch cleanup.
Close issue #4 only when its remaining criteria pass. Search Console account work
is a separate follow-up in NEXT_STEPS.md. Update this prompt for the next batch.
