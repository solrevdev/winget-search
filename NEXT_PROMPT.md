Continue work in /Users/solrevdev/Projects/winget-search.

Read NEXT_STEPS.md first. It is the current agreed roadmap and work/resource log.
IMPROVEMENTS.md contains older notes that may already be resolved.

PR #7 is merged, deployed, and verified live. Its feature branch is deleted.
Master was clean and synced before the PR #5 conflict repair. The task-owned preview servers and Playwright sessions
from the previous round are stopped. Check the resource log and current state
before assuming anything is still running.

Keep hosting free on GitHub Pages, extraction in GitHub Actions, and search in the
browser. Preserve the full packages.json endpoint and existing query/filter URLs.

Propose the next bounded batch before implementing and wait for my agreement.
The next chunk is to finish PR #5 and the useful remaining work in issue #1 as one
SEO change. PR #5's workflow conflict is resolved by merging master at 35bed66
into its existing branch. All 38 Node and nine Python tests pass. The working
branch is feat/seo-meta-sitemap-dataset. Check the remote PR and CI state, and
preserve feat/seo-meta-sitemap-dataset until the PR is merged or otherwise resolved.
Update the existing PR rather than duplicating it.
Further SEO implementation still needs scope approval. Create the later issue #4
maintenance branch from synced master after PR #5 merges and reuse the public URL
rule so the batches do not compete. Recheck mergeability at each PR handoff.
No servers, browsers, background processes, or temporary previews were started
for the conflict repair.

Use the roadmap's findings to check canonical/social metadata, preview assets,
Dataset fields and package count, accurate sitemap dates, semantic markup, and
accessibility. Check current primary-source guidance where needed. Coordinate the
public-base-URL rule with issue #4's redirect work; keep the rest of issue #4 in a
separate maintenance batch. Record Search Console work that needs an account check.
Do not close issues until their acceptance criteria and required live checks pass.

Use subagents for independent implementation or review when helpful. Give each
clear file ownership, tell them others are working in the repo, and require them to
report any resources they start to the parent task.

After scope approval, implement and test the batch. Preserve the 38 Node and nine
Python regressions, add meaningful checks for changed behavior, validate generated
assets, and test affected desktop/mobile flows. Update NEXT_STEPS.md with decisions,
results, remaining work, and the PR link. Leave the PR ready for review. Wait for
approval before merging or deploying; after approval, verify both deployment stages
and the live site before deleting completed branches and syncing master.

Track every server, browser session, background process, and temporary preview as
soon as it starts in NEXT_STEPS.md's resource log. Record ownership, purpose, PID or
tool session ID, browser session name, port/URL, paths, and status. At each PR
handoff, list what remains active and offer to tear it down in one short question.
If cleanup is already authorized, complete it and verify the processes, ports, and
sessions are gone. Preserve unrelated resources. Update the log and this continuation
prompt for the next round.
