# SEO build and review

The site uses static metadata to describe the catalog and its preferred public
URLs. These changes support discovery and sharing; they do not promise a ranking
increase. Search still runs in the browser, extraction runs in GitHub Actions,
and GitHub Pages serves the generated files for free.

## Public URL contract

`site_config.json` holds `public_base_url`, currently
`https://solrevdev.com/winget-search/`. It is the complete HTTPS directory URL,
including any project path. The build normalizes its trailing slash. For another
deployment, change that value or pass `--public-base-url` to `build_site.py`.

The same value controls homepage and agent-page canonical links, Open Graph URLs,
social images, the Dataset download URL, sitemap entries, and the 404 destination.
It does not rewrite search query/filter parameters or change `packages.json`.
Changing this value does not configure DNS or GitHub Pages itself.

Supported forms include a GitHub Pages project path, a user-site root, and a
custom-domain root or subpath. The remaining issue #4 maintenance work must reuse
this rule rather than add another redirect-path setting.

## Catalog metadata and dates

The build requires `metadata.total` to equal the number of package records. It
uses that count in the Dataset description and the visible catalog summary.
`variableMeasured` names actual JSON fields: `id`, `name`, `version`, `publisher`.
Dataset freshness comes from `metadata.extracted_at`, which the extractor writes
in UTC. The full catalog is copied unchanged.

The existing creator, John Smith, matches the public `solrevdev` GitHub profile.
The source repository and upstream manifest repository both use MIT. That catalog
license does not replace the licenses of the individual software packages.
Unverified publication/coverage dates and the repository-as-Dataset `sameAs` claim
are omitted.

The homepage sitemap date follows its latest meaningful source or catalog change.
The agent page follows its source changes, not the daily extraction date. If the
build cannot establish a source date, it omits that date rather than invent one.
The workflow fetches source history for these dates.

## Deliberate omissions

- Google ignores the keywords meta tag, so issue #1's suggestion is not applied.
- `numberOfItems` belongs to `ItemList`, not `Dataset`; a plain description gives
  the count without misusing the schema.
- Google ignores sitemap `priority` and `changefreq`; neither is generated.
- A project-path `robots.txt` cannot control the host root. Any root-level sitemap
  declaration belongs to the owner of `https://solrevdev.com/robots.txt`.
- Query/filter combinations keep the homepage canonical. This batch does not
  create indexable package detail pages.

## Review and release

Run the Node and Python suites described in `NEXT_STEPS.md`. Build a preview with
a real catalog outside the checkout:

```sh
python build_site.py --packages /path/to/packages.json --output-dir /path/to/preview/winget-search
```

Check generated HTML, JSON-LD, sitemap XML, the social PNG and its SVG source.
Run `tests/browser-search.js` and `tests/browser-seo.js` against that preview at
desktop/mobile widths, including keyboard use. Keep test tools and downloaded
catalogs outside the committed site. Record evidence and resources in
`NEXT_STEPS.md`.

After merge approval, verify both Build and Deploy and Pages publication, then
check the live canonical/social tags, catalog count and dates, sitemap, image,
redirect, and search flows. Keep issues open until their remaining criteria pass.

Search Console needs an account check after deployment: submit or confirm
`https://solrevdev.com/winget-search/sitemap.xml`, inspect both public pages, and
check the old Dataset creator/license validation status. The old PR's report that
validation had started is historical evidence, not a current result. Run Google's
Rich Results Test on the deployed homepage too.

## Primary guidance checked

- [Google Dataset structured data](https://developers.google.com/search/docs/appearance/structured-data/dataset)
- [Google canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google sitemap dates](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)
- [Schema.org numberOfItems](https://schema.org/numberOfItems)
- [Open Graph image and alt properties](https://ogp.me/)
- [Public creator profile](https://github.com/solrevdev)
- [Upstream manifest license](https://github.com/microsoft/winget-pkgs/blob/master/LICENSE)
