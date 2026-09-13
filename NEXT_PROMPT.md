Continue work in /Users/solrevdev/Projects/winget-search.

Read NEXT_STEPS.md first, then this file. SEO.md records the public URL contract,
SEO decisions, primary sources and release checks. IMPROVEMENTS.md is historical.

PR #7 is merged, deployed and verified. PR #5's conflict repair is c5de9d1.
The user approved the SEO batch for PR #5 plus useful issue #1 work. Implementation
and local checks are complete on feat/seo-meta-sitemap-dataset in the existing
PR #5. Check its current head, CI and mergeability before acting.

Wait for explicit merge/deployment approval. No deployment or issue closure was
authorized for this handoff. After approval, merge and verify both Build and Deploy
and Pages publication, then live metadata, catalog counts/dates, sitemap, preview
image, redirect and desktop/mobile search. Preserve the feature branch until that
verification passes; then remove it and sync master.

All 38 Node tests pass. All nine Python extraction regressions plus ten build tests
pass (19 Python total). Generated HTML/JSON-LD/XML/images and workflow checks pass.
Search and SEO browser suites pass at 1280px and 375px. Axe light/dark page and Copy
state checks pass after fixing contrast and keyboard access. Review NEXT_STEPS.md
for evidence and resource status. All PR #5 servers/browser sessions are stopped;
temporary evidence is inert. Preserve unrelated resources.

Keep GitHub Pages hosting free, extraction in Actions, and search in the browser.
Preserve packages.json and query/filter URLs. site_config.json's public_base_url
feeds build_site.py's metadata, sitemap, guide examples and 404 destination.

PR #5 includes only the shared URL/redirect portion of issue #4. Keep README,
cache/default-branch logic and force_pages_update.sh maintenance separate. Start
that later branch from synced master after PR #5 merges, reuse its URL rule and
check mergeability again. Propose the next bounded batch and await agreement.

Search Console still needs an account check for sitemap submission, URL indexing,
and the old Dataset creator/license validation status. Run Rich Results Test on
the deployed homepage. Do not close issues before their remaining criteria and
required live checks pass.

Use subagents when useful with clear file ownership; they must report resources
to the parent. Record any server, browser, background job or preview immediately
in NEXT_STEPS.md with owner, purpose, PID/tool session, browser name, port/URL,
paths and status. At handoff list active resources and offer cleanup; perform any
already-authorized cleanup and verify it. Update both handoff files each round.
