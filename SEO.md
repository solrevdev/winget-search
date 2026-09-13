# SEO contract

Static metadata supports discovery and sharing. Search runs in the browser,
extraction runs in Actions, and GitHub Pages serves the generated site for free.

## Public URLs

`site_config.json` sets `public_base_url`, currently
`https://solrevdev.com/winget-search/`. It must be a complete HTTPS directory URL;
`build_site.py` normalizes the trailing slash. Override it with `--public-base-url`
for another deployment. Root sites, project paths and custom domains are supported.

This single value controls canonical/social URLs, images, Dataset downloads,
sitemap entries, guide examples and the 404 destination. Issue #4 must reuse it. Changing it does
not configure DNS or Pages. Query/filter URLs keep the homepage canonical;
`packages.json` and browser search state remain unchanged.

## Dataset and dates

The build requires `metadata.total` to match the package record count and uses it
in the Dataset description and visible summary. `variableMeasured` names actual
fields: `id`, `name`, `version`, `publisher`. Freshness uses the extractor's UTC
`metadata.extracted_at`. The catalog is copied unchanged.

Creator John Smith matches the public profile. The catalog's MIT license does not
replace individual software licenses. Unverified publication/coverage dates and a
repository-as-Dataset `sameAs` claim are omitted.

Homepage sitemap dates follow meaningful source or catalog changes; the agent page
follows its source changes. Unknown source dates are omitted. Builds fetch Git
history. Omit ignored keywords, sitemap `priority`/`changefreq`, and Dataset
`numberOfItems` (an `ItemList` property). A project-path `robots.txt` cannot control
the host root; any root sitemap declaration needs the domain owner's action.

## Account follow-up

After deployment, use Search Console to submit or confirm
`https://solrevdev.com/winget-search/sitemap.xml`, inspect both public pages, and
check Dataset creator/license validation. A historical validation request is not a
current result. Check the public homepage in Google's Rich Results Test too.
Follow the [release checks](README.md#work-across-sessions); keep active resources
in [NEXT_PROMPT.md](NEXT_PROMPT.md).

## Sources

- [Google Dataset fields](https://developers.google.com/search/docs/appearance/structured-data/dataset), [canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google sitemap dates](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap), [supported meta tags](https://developers.google.com/search/docs/crawling-indexing/special-tags)
- [Schema.org numberOfItems](https://schema.org/numberOfItems), [Open Graph properties](https://ogp.me/)
- [Creator profile](https://github.com/solrevdev), [upstream license](https://github.com/microsoft/winget-pkgs/blob/master/LICENSE)
