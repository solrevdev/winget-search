# WinGet Package Search

Search Windows Package Manager packages at
[solrevdev.com/winget-search](https://solrevdev.com/winget-search/).
GitHub Actions extracts the catalog daily at 02:00 UTC. GitHub Pages hosts the
static site for free; search runs in your browser.

## Features

- Search IDs, names, monikers, descriptions, publishers and tags, with exact
  matches first and typo fallback when needed.
- Filter by publisher and tags; share or reload query and filter URLs.
- Copy an exact-ID `winget install` command and expand Details for package metadata.
- Browse 25 results at a time, up to 200 matches; use `/` to search and `Esc` to clear.
- Use the full [catalog API](https://solrevdev.com/winget-search/packages.json),
  [query guide](https://solrevdev.com/winget-search/agent-access.html) or
  [agent instructions](https://solrevdev.com/winget-search/llms.txt).

English fields supplement each package's default locale. The catalog keeps one
version per package. Selection keeps Python packaging's version order and also
recognizes ISO dates and numeric `A@B` versions. Other formats rank below recognized
versions, with numeric-aware text ordering and fixed tie-breaks. This fallback is
predictable but cannot infer every publisher's release order. The catalog retains
the original version values.

## Setup and deployment

1. Fork or clone the repository. Keep source work on `master`; `gh-pages` holds
   generated files. The build also accepts pushes to `main` for forks using it.
2. Set `public_base_url` in [site_config.json](site_config.json) for your deployment.
   [build_site.py](build_site.py) uses it for metadata, guides, the sitemap and
   the 404 redirect. See [SEO.md](SEO.md) for the URL contract. Update the repository
   link in the footer when forking. Configure any custom domain separately.
3. Enable GitHub Actions and permit the actions used by the workflows. The build
   requests write access for the built-in `GITHUB_TOKEN`; no personal token is
   needed. Repository or organization policy must allow those permissions.
4. Push to the source branch or run **Build and Deploy** from the Actions tab.
   It refreshes `microsoft/winget-pkgs`, extracts `packages.json`, runs the shared
   site builder and pushes the result to `gh-pages`.
5. Enable **Settings > Pages > Deploy from a branch**, with `gh-pages` and `/ (root)`.
   The build does not enable Pages or change this setting.
6. Check both **Build and Deploy** and the separate **Pages** publication, then
   open the live site. A successful push to `gh-pages` alone does not prove that
   Pages published the site.

The upstream Git checkout uses a versioned UTC daily cache key with prefix restore.
Every build refreshes it, including exact cache hits, using upstream's current
default branch. Same-day runs reuse the saved snapshot; the next day can restore
it by prefix and save a fresh snapshot.

To refresh the catalog, run **Build and Deploy**. For a publication-only retry,
run **Trigger Pages Deploy**. The local alternative is `bash force_pages_update.sh`
from a clean checkout on a branch. It fetches `gh-pages` into a temporary worktree,
allows only fast-forward updates and pushes changes to `index.html` and `.nojekyll`.
Your starting checkout stays in place, including on failure. Detached HEAD and
tracked or untracked changes cause it to stop. On failure, it prints the retained
worktree path for inspection; remove that exact worktree with `git worktree remove`
once its contents are no longer needed. It never force-pushes over a newer build.

If the site is missing or stale, check Pages settings, both workflow results and
the deployed files before testing with a hard browser refresh.

## Development

Use Python 3.11 or later, Node.js 22 or later and an isolated Python environment:

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.cjs
git diff --check
```

Without `uv`, use `python3 -m venv .venv`, then
`.venv/bin/python -m pip install -r requirements.txt`.

Keep downloaded catalogs and previews outside the source checkout. For example:

```sh
preview_root=$(mktemp -d)
git clone --depth 1 https://github.com/microsoft/winget-pkgs.git "$preview_root/winget-pkgs"
.venv/bin/python extract_packages.py "$preview_root/winget-pkgs/manifests" "$preview_root/packages.json"
.venv/bin/python build_site.py --packages "$preview_root/packages.json" --output-dir "$preview_root/site"
.venv/bin/python -m http.server 8000 --bind 127.0.0.1 --directory "$preview_root/site"
```

Open `http://127.0.0.1:8000`. Stop the server when finished and keep track of the
printed temporary path. The source `packages.json` is a tracked empty placeholder;
the build publishes the generated catalog without changing its public format.

The Node tests cover search logic, ranking and UI state. Python tests cover
extraction, site builds and maintenance. Pull requests run both suites.
`tests/browser-search.js` and `tests/browser-seo.js` check desktop and mobile flows
through `playwright-cli run-code --filename` against a built preview or the live site.

## Work across sessions

[IMPROVEMENTS.md](IMPROVEMENTS.md) is the only backlog.
[NEXT_PROMPT.md](NEXT_PROMPT.md) is the paste-ready handoff for the current or next
task: scope, approval state, next action and active resources. Replace it as work
moves on. Ask before adding backlog items; report any follow-up found during PR
review before adding it. When the list is empty, agree a fresh scan.

Verify local Git and GitHub before acting. Start new work from synced `master` on
a fresh branch; resume an existing task on its verified branch. Preserve the
catalog format, search, query/filter URLs, ranking, copy and Details. Keep the
existing regression tests and checkout cache smoke test. Run the commands above;
CI also runs `tests/checkout-cache-smoke.py` against the checkout action bundle.
For affected site flows, build with `build_site.py` and run both browser suites at
desktop and mobile widths. Read `playwright-cli --help` before use.

Leave a tested PR and wait for merge approval. After merge, verify Build and
Deploy, separate Pages publication and the live site before closing issues or
deleting completed branches. Keep dated release evidence in the PR or issue;
past checks do not establish current status. Docs-only commits may use `[skip ci]`
after checking that no deployed inputs changed.

Track task-owned resources in the handoff as they start: purpose, paths,
PID/session, URL/port and status. After release checks, stop and remove only those
resources and clear completed entries from the handoff. Keep unrelated backlog,
account work, processes and files separate.

## Source guide

| File | Purpose |
| --- | --- |
| `index.html`, `search.js`, `vendor/` | Search UI, ranking and bundled search library |
| `extract_packages.py` | Manifest extraction and locale merging |
| `build_site.py`, `site_config.json` | Shared site build and public URL |
| `agent-access.html`, `llms.txt`, `sitemap.xml` | Source templates for generated guides and sitemap |
| `.github/workflows/` | Tests, daily build and publication retry |
| `IMPROVEMENTS.md` | Remaining work awaiting scope agreement |
| `NEXT_PROMPT.md` | Current or next task handoff and active resources |

Change the daily schedule in `.github/workflows/github_workflows_build.yml`.
Change styles in `index.html`; retain search and URL contracts when editing the UI.
See [IMPROVEMENTS.md](IMPROVEMENTS.md) for the remaining backlog.

## License and credits

Project code uses the [MIT license](license.txt). Package data comes from
[microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs); individual
software packages retain their own licenses. GitHub Actions, GitHub Pages and
[peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)
handle the build and deployment.
