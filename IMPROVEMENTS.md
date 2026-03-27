# Improvements & To-Do

This document captures known bugs, quick wins, and feature ideas for the winget-search project.
It is intended as a starting point for new contributors or an LLM asked to find work to do.

Each item notes which file(s) are affected, the effort involved, and whether the change is
backend-only (Python / CI), frontend-only (index.html), or both.

## Branch Progress Update (2026-02-26)

This section tracks what is already implemented on branch `codex/frontend-search-improvements`
so future contributors/LLMs can continue from the remaining items.

### Completed In This Branch

- `#1` Regex crash fix in `highlightMatch()` (escaped regex input)
- `#5` Minified JSON output in `extract_packages.py` (`separators=(",", ":")`)
- `#6` Ranked/weighted search scoring in frontend
- `#7` `shortDescription` fallback in result rendering
- `#8` Incremental result rendering with `Load more` paging
- `#9` URL search state support (`?q=`) + back/forward handling
- `#10` Homepage link + license badge shown in cards
- `#11` Click-to-filter for publisher and tags
- `#26` Removed unused `re` import and unused `is_english_manifest()` helper

### Current Status By Item

| # | Status on this branch | Notes / next step |
|---|---|---|
| 1 | Done | `highlightMatch()` now escapes regex tokens before `RegExp` creation. |
| 2 | Open | CI cache key still uses `${{ github.run_id }}` and misses cache reuse. |
| 3 | Open | Footer still has `YOUR_USERNAME/YOUR_REPO_NAME` placeholder URL. |
| 4 | Open | README still has duplicated summary/malformed opening heading block. |
| 5 | Done | `packages.json` output no longer pretty-printed. |
| 6 | Done | Weighted ranking added; exact/prefix/id/name matches now rank higher. |
| 7 | Done | Description fallback now uses `pkg.description || pkg.shortDescription`. |
| 8 | Done | Results render in pages of 25 with a `Load more` button. |
| 9 | Done | Search query is read/written from URL query string. |
| 10 | Done | Homepage and license are rendered in result cards. |
| 11 | Done | Publisher/tags are interactive filters feeding back into search. |
| 12 | Open | No compact/expandable details modal yet. |
| 13 | Open | No copy-command variants UI yet. |
| 14 | Open | No fuzzy/typo-tolerant search dependency integrated yet. |
| 15 | Open | No pre-built backend search index artifact yet. |
| 16 | Open | No inferred package categories generated/displayed yet. |
| 17 | Open | Template leftover config files still present. |
| 18 | Open | `license.txt` still has placeholder copyright holder. |
| 19 | Open | 404 redirect path is still hardcoded in workflow. |
| 20 | Open | Cached winget update still resets to `origin/master`. |
| 21 | Open | `force_pages_update.sh` still assumes return branch `master`. |
| 22 | Open | README license link/file mismatch still unresolved. |
| 23 | Open | README still describes stricter locale behavior than extractor implements. |
| 24 | Open | Version fallback logic still collapses non-PEP440 versions to `0.0.0`. |
| 25 | Open | `packages.json` tracking policy remains ambiguous. |
| 26 | Done | Dead code/import cleanup completed in extractor. |

### Suggested Next Low-Risk Work (Recommended Order)

1. `#3` Replace placeholder repository URL in footer (`index.html`).
2. `#4` Clean up duplicate README summary + malformed heading.
3. `#22` Fix README license link mismatch (`LICENSE` vs `license.txt`).
4. `#2` Improve CI cache key strategy (date-based key + restore keys).
5. `#20` Make cached winget reset use detected default branch.
6. `#19` Remove hardcoded 404 redirect repo path.
7. `#21` Make `force_pages_update.sh` restore original branch.

### Workflow Safety Note For This Branch

`github_workflows_build.yml` runs on push to `main`/`master`, on schedule, and via manual dispatch.
Pushing `codex/frontend-search-improvements` should not trigger that workflow automatically.

### Pages Configuration Note (2026-03-27)

GitHub Pages must remain enabled for this repository and must serve from the `gh-pages`
branch root. A successful `Build and Deploy` run only updates the deployment branch; it does
not re-enable Pages if the repository-level Pages setting has been turned off.

Practical consequence: if `gh-pages` contains the expected `index.html`/`packages.json`
artifacts but `https://solrevdev.com/winget-search/` returns `404`, check **Settings** >
**Pages** before assuming a frontend regression.

---

## Bugs

### 1. Regex crash on special characters in search input
**File:** `index.html` — `highlightMatch()` function
**Priority:** High (crashes the page on certain inputs)

The search query is passed directly into `new RegExp()` without escaping regex special characters.
A query like `(test` or `a.b` throws a `SyntaxError` and breaks highlighting for that keystroke.

**Fix:**
```javascript
// Before
const regex = new RegExp(`(${query})`, 'gi');

// After
const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const regex = new RegExp(`(${escaped})`, 'gi');
```

---

### 2. GitHub Actions cache key never hits
**File:** `.github/workflows/github_workflows_build.yml`
**Priority:** Medium (wastes CI time, not a correctness bug)

The cache key for the `winget-pkgs` clone is `winget-pkgs-${{ github.run_id }}`, which is unique
per run and will never produce a cache hit on scheduled runs. The winget repo is always cloned
fresh, negating the cache entirely.

**Fix:** Use a date-based key so same-day retries reuse the clone:
```yaml
- name: Get date for cache key
  id: date
  run: echo "date=$(date +'%Y-%m-%d')" >> $GITHUB_OUTPUT

- name: Cache winget-pkgs
  uses: actions/cache@v4
  with:
    path: winget-pkgs
    key: winget-pkgs-${{ steps.date.outputs.date }}
    restore-keys: winget-pkgs-
```

---

### 3. Placeholder URLs never replaced in index.html
**File:** `index.html` — footer section (around line 317)
**Priority:** Medium (broken link on live site)

The footer contains `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME` which should have been
replaced with the actual repository URL during initial setup. The README documents this step
but it was not done.

**Fix:** Replace the placeholder with the real repository URL in the footer link.

---

### 4. Duplicate Summary section in README
**File:** `README.md` — lines 1–8 and lines 246–254
**Priority:** Low (cosmetic)

The summary paragraph appears twice: once before the `#` heading (likely an authoring mistake)
and once near the end under a second `## Summary` heading. Remove one of them.

---

## Performance

### 5. Minify packages.json output
**File:** `extract_packages.py` — `json.dump()` call near the end of `main()`
**Priority:** High (easy 30–40% reduction in payload size)

The JSON is written with `indent=2`, adding whitespace for human readability. With 30,000+
packages this is unnecessary overhead for a file that is only consumed by a browser.

**Fix:**
```python
# Before
json.dump(output, f, cls=EnhancedJSONEncoder, ensure_ascii=False, indent=2)

# After
json.dump(output, f, cls=EnhancedJSONEncoder, ensure_ascii=False, separators=(',', ':'))
```

---

### 6. Add ranked/weighted search results
**File:** `index.html` — `showResults()` function
**Priority:** High (meaningfully improves result quality)

All substring matches are treated equally. A package whose `id` exactly matches the query ranks
the same as one where the query appears in the middle of a long description.

**Fix:** Score each package and sort descending before slicing to 100:
```javascript
function scorePackage(pkg, q) {
  let score = 0;
  if (pkg.id?.toLowerCase() === q)               score += 100;
  else if (pkg.id?.toLowerCase().startsWith(q))  score += 50;
  else if (pkg.id?.toLowerCase().includes(q))    score += 20;
  if (pkg.name?.toLowerCase().includes(q))       score += 15;
  if (pkg.tags?.some(t => t?.toLowerCase().includes(q))) score += 8;
  if (pkg.publisher?.toLowerCase().includes(q))  score += 5;
  if (pkg.description?.toLowerCase().includes(q)) score += 3;
  return score;
}

// In showResults(), replace the filter+slice with:
results = packages
  .map(pkg => ({ pkg, score: scorePackage(pkg, q) }))
  .filter(({ score }) => score > 0)
  .sort((a, b) => b.score - a.score)
  .slice(0, 100)
  .map(({ pkg }) => pkg);
```

---

### 7. Use shortDescription as fallback when description is empty
**File:** `index.html` — result card template inside `renderPackage()` (or equivalent)
**Priority:** Medium (data completeness, backend already extracts the field)

The Python extractor outputs both `description` (from the locale file) and `shortDescription`
(from the version manifest), but the frontend only uses `description`. Many packages have an
empty `description` but a populated `shortDescription`.

**Fix:** In the result card template, change:
```javascript
// Before
${pkg.description ? `<p class="description">${escapeHtml(pkg.description)}</p>` : ''}

// After
const desc = pkg.description || pkg.shortDescription || '';
// then use desc in the template
```

---

### 8. Virtual scrolling / "Load more" button
**File:** `index.html` — `showResults()` and the results container
**Priority:** Medium (performance on low-end devices)

Results are capped at 100, but rendering 100 DOM nodes at once can still cause layout jank on
lower-end hardware. The simplest fix is a "Load more" button that appends the next batch rather
than a full virtual-scroll implementation:

```javascript
const PAGE_SIZE = 25;
let visibleCount = PAGE_SIZE;

function renderPage() {
  const visible = currentResults.slice(0, visibleCount);
  resultsDiv.innerHTML = visible.map(renderCard).join('');
  if (visibleCount < currentResults.length) {
    resultsDiv.insertAdjacentHTML('beforeend',
      `<button onclick="loadMore()">Load more (${currentResults.length - visibleCount} remaining)</button>`);
  }
}

function loadMore() {
  visibleCount += PAGE_SIZE;
  renderPage();
}
```

---

## Features

### 9. URL-based search state (?q=query)
**File:** `index.html` — search input event listener and page initialisation
**Priority:** High (enables sharing search results, browser back/forward)

Currently there is no way to share a search URL or navigate back to a previous search.

**Fix:** Read from and write to the URL query string:
```javascript
// On page load, after packages are ready:
const params = new URLSearchParams(location.search);
if (params.has('q')) {
  searchInput.value = params.get('q');
  showResults(params.get('q'));
}

// In the debounced input handler:
history.replaceState(null, '', query ? `?q=${encodeURIComponent(query)}` : location.pathname);
```

---

### 10. Display homepage and license fields
**File:** `index.html` — result card template
**Priority:** Medium (zero backend cost, fields already in packages.json)

The Python extractor outputs `homepage` and `license` for every package but neither is shown
in the UI. Adding them to the card requires only a frontend template change.

**Fix:**
```javascript
${pkg.homepage ? `<a href="${escapeHtml(pkg.homepage)}" target="_blank" rel="noopener noreferrer">Homepage</a>` : ''}
${pkg.license ? `<span class="license-badge">${escapeHtml(pkg.license)}</span>` : ''}
```

- `homepage` — link with `rel="noopener noreferrer"` and `target="_blank"`
- `license` — small badge rendered alongside the version badge

---

### 11. Click-to-filter by publisher or tag
**File:** `index.html` — publisher span and tag pill click handlers
**Priority:** Medium (discoverability, frontend-only)

Publisher names and tag pills are currently rendered as plain text or non-interactive spans.
Clicking them should populate the search box with that value and trigger a new search.

**Fix:** Add an `onclick` to each:
```javascript
// Publisher
`<span class="publisher" onclick="filterBy('${escapeHtml(pkg.publisher)}')">${escapeHtml(pkg.publisher)}</span>`

// Tag pill
`<span class="tag" onclick="filterBy('${escapeHtml(tag)}')">${escapeHtml(tag)}</span>`

// Helper
function filterBy(value) {
  searchInput.value = value;
  showResults(value);
  searchInput.focus();
}
```

---

### 12. Package detail expansion / modal
**File:** `index.html`
**Priority:** Medium (reduces visual clutter in the default list view)

Cards currently show all fields inline. A compact default view with an expandable section (or
modal) for full description, all tags, homepage, and license would make the list easier to scan.

No backend changes needed.

---

### 13. Copy command variants
**File:** `index.html` — copy button area
**Priority:** Low (power user feature)

The README lists "Add copy as PowerShell option" as a future idea. A toggle or secondary button
could offer:

| Variant | Command |
|---|---|
| Standard (current) | `winget install -e --id Publisher.Name` |
| Silent / scripted | `winget install --exact --id Publisher.Name --silent --accept-package-agreements` |

A small segmented toggle above the results (or per-card) is sufficient. No backend changes needed.

---

### 14. Fuzzy / typo-tolerant search
**File:** `index.html`
**Priority:** Low (significant UX improvement but requires a new dependency)

Simple substring matching misses common typos (e.g., `googel chrome`). A lightweight client-side
full-text search library such as [FlexSearch](https://github.com/nextapps-de/flexsearch) or
[Fuse.js](https://fusejs.io/) would add typo tolerance and tokenised indexing.

Both can be included as a single self-hosted minified file — no npm or build step required.
FlexSearch is generally faster for large datasets; Fuse.js is simpler to configure.

The index would be built once after `packages.json` is fetched, then reused for all queries.

---

### 15. Pre-built search index (backend)
**File:** `extract_packages.py`, `index.html`
**Priority:** Low (more complex, high payoff at scale)

Instead of building the search index in the browser on every page load, generate a serialised
inverted index at extraction time in Python and ship it as a separate `index.json` file.
The browser loads the index lazily and searches it directly, avoiding the O(n) full-array scan.

---

### 16. Inferred package categories (backend)
**File:** `extract_packages.py`, `index.html`
**Priority:** Low (enables filter-by-category in the UI)

Winget manifests have no category field, but one can be inferred from the `Tags` list using a
mapping table in Python (e.g., tags containing `browser` → `Web Browsers`). The category would
be emitted as a new field in `packages.json` and surfaced as a filter panel in the UI.

---

## Housekeeping

### 17. Remove irrelevant config files
**Files:** `.editorconfig`, `omnisharp.json`, `.dockerignore`
**Priority:** Low (cosmetic, no functional impact)

- `.editorconfig` is configured for C#/.NET (indent style, charset settings for `.cs` files)
- `omnisharp.json` is an OmniSharp C# language server config — not used by this project
- `.dockerignore` exists but there is no `Dockerfile`

These are likely leftovers from a project template. They can be removed or replaced with
configs appropriate for a Python + HTML project.

---

### 18. Personalise license.txt
**File:** `license.txt`
**Priority:** Low (cosmetic)

The copyright holder is listed as `[Your Name]`. Replace with the actual author name.

---

## Summary Table

| # | Description | File(s) | Type | Priority |
|---|---|---|---|---|
| 1 | Fix regex crash in `highlightMatch` | `index.html` | Bug | **High** |
| 2 | Fix CI cache key (never hits) | `build.yml` | Bug | Medium |
| 3 | Replace placeholder repo URL in footer | `index.html` | Bug | Medium |
| 4 | Remove duplicate Summary in README | `README.md` | Bug | Low |
| 5 | Minify `packages.json` output | `extract_packages.py` | Performance | **High** |
| 6 | Ranked/weighted search results | `index.html` | Performance | **High** |
| 7 | Use `shortDescription` as fallback | `index.html` | Performance | Medium |
| 8 | Virtual scrolling / "Load more" button | `index.html` | Performance | Medium |
| 9 | URL-based search state (`?q=`) | `index.html` | Feature | **High** |
| 10 | Show `homepage` + `license` fields | `index.html` | Feature | Medium |
| 11 | Click-to-filter by publisher or tag | `index.html` | Feature | Medium |
| 12 | Package detail expansion / modal | `index.html` | Feature | Medium |
| 13 | Copy command variants | `index.html` | Feature | Low |
| 14 | Fuzzy / typo-tolerant search | `index.html` | Feature | Low |
| 15 | Pre-built search index (backend) | `extract_packages.py` + `index.html` | Feature | Low |
| 16 | Inferred package categories | `extract_packages.py` + `index.html` | Feature | Low |
| 17 | Remove irrelevant config files | `.editorconfig`, `omnisharp.json`, `.dockerignore` | Housekeeping | Low |
| 18 | Personalise `license.txt` | `license.txt` | Housekeeping | Low |

---

## Validation Audit (2026-02-20)

The list above was validated against the current repository state.

| # | Status | Validation notes |
|---|---|---|
| 1 | Confirmed | `highlightMatch()` still creates `RegExp` from unescaped input (`index.html:389`). |
| 2 | Confirmed | Cache key still uses `${{ github.run_id }}` (`.github/workflows/github_workflows_build.yml:36`). |
| 3 | Confirmed | Footer still contains `YOUR_USERNAME/YOUR_REPO_NAME` placeholder (`index.html:316`). |
| 4 | Confirmed | Duplicate summary still present (`README.md:1` and `README.md:246`); top heading is also malformed (`README.md:9`). |
| 5 | Confirmed | JSON output is still pretty-printed with `indent=2` (`extract_packages.py:167`). |
| 6 | Confirmed | Search still does unranked substring filter + `slice(0, 100)` (`index.html:400-410`). |
| 7 | Partially confirmed | UI only uses `pkg.description` (`index.html:439`), but extractor already sets description fallback from locale `ShortDescription` (`extract_packages.py:78`). Fallback to package-level `shortDescription` is still useful. |
| 8 | Confirmed | Rendering still injects all returned cards at once (`index.html:423-455`). |
| 9 | Confirmed | No URL query-state persistence exists. |
| 10 | Confirmed | `homepage` and `license` are extracted (`extract_packages.py:79-80`) but not shown in UI. |
| 11 | Confirmed | Publisher/tags are non-interactive spans (`index.html:427`, `index.html:440-441`). |
| 12 | Confirmed | No expandable details/modal exists. |
| 13 | Confirmed | Only one command variant is rendered (`index.html:424`). |
| 14 | Confirmed | Search is exact substring only (no fuzzy matching). |
| 15 | Confirmed | No pre-built backend search index artifact exists. |
| 16 | Confirmed | No inferred category field is generated. |
| 17 | Partially confirmed | Files are mostly template leftovers, but removal is optional rather than mandatory. |
| 18 | Confirmed | `license.txt` still contains `[Your Name]` placeholder (`license.txt:3`). |

---

## Additional Improvements Found In Code Review

### 19. Hardcoded 404 redirect path breaks forks/custom repo names
**File:** `.github/workflows/github_workflows_build.yml` (line ~98)  
**Priority:** High

The generated 404 page always redirects to `/winget-search/`, which fails for repos with different names.

**Fix:** build from repository name:
```yaml
- name: Copy site assets
  run: |
    repo_name="${{ github.event.repository.name }}"
    echo "<!DOCTYPE html><html><head><meta http-equiv=\"refresh\" content=\"0; url=/${repo_name}/\"></head></html>" > deploy/404.html
```

---

### 20. Cached winget update hardcodes `origin/master`
**File:** `.github/workflows/github_workflows_build.yml` (line ~53)  
**Priority:** Medium

If upstream default branch ever differs from `master`, cached update can break.

**Fix:** resolve default branch dynamically:
```bash
default_branch=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git reset --hard "origin/$default_branch"
```

---

### 21. `force_pages_update.sh` assumes return branch is `master`
**File:** `force_pages_update.sh` (line ~25)  
**Priority:** Low

Script always checks out `master` at the end, which is wrong on `main`-based repos.

**Fix:** capture and restore the original branch:
```bash
start_branch=$(git rev-parse --abbrev-ref HEAD)
# ... run script steps ...
git checkout "$start_branch"
```

---

### 22. README license link points to missing filename
**Files:** `README.md` (line ~258), `license.txt`  
**Priority:** Low

README links to `[MIT License](LICENSE)` but file is named `license.txt`.

**Fix:** rename file to `LICENSE` or update README link to `license.txt`.

---

### 23. "English-only" docs do not match extraction behavior
**Files:** `README.md`, `extract_packages.py`  
**Priority:** Medium

README claims English-only extraction, but extractor falls back to non-`en-US` locale files when needed (`extract_packages.py:68-70`).

**Fix options:**
- enforce strict `en-US` only in code, or
- update README to describe current fallback behavior.

---

### 24. Non-PEP440 version fallback can pick wrong "latest"
**File:** `extract_packages.py` (`parse_version`)  
**Priority:** Medium

Invalid versions currently collapse to `0.0.0`; multiple non-standard versions compare equal, making latest-selection unreliable.

**Fix:** compare with a deterministic fallback key:
```python
def version_key(ver_str: str):
    try:
        return (0, version.parse(ver_str), "")
    except Exception:
        return (1, None, ver_str)
```

---

### 25. `packages.json` tracking policy is ambiguous
**Files:** `packages.json`, `.gitignore` (line ~428)  
**Priority:** Low

`packages.json` is tracked in git, but `.gitignore` also lists it. This can confuse contributor expectations.

**Fix:** decide one policy explicitly:
- generated artifact only (stop tracking file), or
- tracked sample file (remove ignore entry).

---

### 26. Unused code/import in extractor
**File:** `extract_packages.py`  
**Priority:** Low

`is_english_manifest()` is unused and `re` import is unused.

**Fix:** remove dead code/imports, or wire the helper into real filtering.

---

## Addendum Summary Table (New Items Only)

| # | Description | File(s) | Type | Priority |
|---|---|---|---|---|
| 19 | Remove hardcoded 404 path | `.github/workflows/github_workflows_build.yml` | Bug | **High** |
| 20 | Remove hardcoded `origin/master` dependency | `.github/workflows/github_workflows_build.yml` | Bug | Medium |
| 21 | Make `force_pages_update.sh` branch-safe | `force_pages_update.sh` | Bug | Low |
| 22 | Fix README license filename mismatch | `README.md`, `license.txt` | Bug | Low |
| 23 | Align docs with locale fallback behavior | `README.md`, `extract_packages.py` | Bug | Medium |
| 24 | Improve non-standard version comparison | `extract_packages.py` | Bug | Medium |
| 25 | Clarify `packages.json` tracking policy | `packages.json`, `.gitignore` | Housekeeping | Low |
| 26 | Remove dead code/imports | `extract_packages.py` | Housekeeping | Low |
