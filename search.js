(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./vendor/minisearch-7.2.0.js'));
  } else {
    root.WingetSearch = factory(root.MiniSearch);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (MiniSearch) {
  'use strict';

  function tokenizeQuery(query) {
    return String(query || '')
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
  }

  function normalizeSearchQuery(query) {
    const normalized = tokenizeQuery(query).join(' ');
    const aliases = { 'vs code': 'vscode' };
    return Object.hasOwn(aliases, normalized) ? aliases[normalized] : normalized;
  }

  function scorePackage(pkg, queryLower, tokens) {
    const id = (pkg.id || '').toLowerCase();
    const name = (pkg.name || '').toLowerCase();
    const moniker = String(pkg.moniker ?? '').toLowerCase();
    const publisher = (pkg.publisher || '').toLowerCase();
    const description = `${pkg.shortDescription || ''} ${pkg.description || ''}`.toLowerCase();
    const tags = Array.isArray(pkg.tags)
      ? pkg.tags.filter(tag => typeof tag === 'string').map(tag => tag.toLowerCase())
      : [];

    const searchable = `${id} ${name} ${moniker} ${publisher} ${description} ${tags.join(' ')}`;
    if (!tokens.every(token => searchable.includes(token))) {
      return 0;
    }

    // Extra description and tag matches must not outrank an exact ID, moniker, or name.
    let tier = 1;
    if (id === queryLower) tier = 6;
    else if (moniker === queryLower) tier = 5;
    else if (name === queryLower) tier = 4;
    else if ([id, name, moniker].some(value => value.startsWith(queryLower))) tier = 3;
    else if ([id, name, moniker].some(value => value.includes(queryLower))) tier = 2;

    let score = 0;

    if (id === queryLower) score += 120;
    else if (id.startsWith(queryLower)) score += 90;
    else if (id.includes(queryLower)) score += 60;

    if (name === queryLower) score += 90;
    else if (name.startsWith(queryLower)) score += 70;
    else if (name.includes(queryLower)) score += 40;

    if (publisher.includes(queryLower)) score += 18;
    if (description.includes(queryLower)) score += 14;
    if (tags.some(tag => tag === queryLower)) score += 25;
    else if (tags.some(tag => tag.includes(queryLower))) score += 12;

    for (const token of tokens) {
      if (id.startsWith(token)) score += 8;
      else if (id.includes(token)) score += 4;
      if (name.includes(token)) score += 4;
      if (publisher.includes(token)) score += 2;
      if (description.includes(token)) score += 1;
      if (tags.some(tag => tag.includes(token))) score += 2;
    }

    return tier * 1000 + Math.min(score, 999);
  }

  function normalizeFilters(filters = {}) {
    const publisher = typeof filters?.publisher === 'string' ? filters.publisher.trim() : '';
    const seen = new Set();
    const tags = (Array.isArray(filters?.tags) ? filters.tags : [])
      .filter(tag => typeof tag === 'string')
      .map(tag => tag.trim())
      .filter(tag => {
        const key = tag.toLowerCase();
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    return { publisher, tags };
  }

  function matchesNormalizedFilters(pkg, filters) {
    if (filters.publisher && String(pkg.publisher ?? '').trim().toLowerCase() !== filters.publisher.toLowerCase()) {
      return false;
    }
    const tags = Array.isArray(pkg.tags)
      ? pkg.tags.filter(tag => typeof tag === 'string').map(tag => tag.trim().toLowerCase())
      : [];
    return filters.tags.every(tag => tags.includes(tag.toLowerCase()));
  }

  function matchesFilters(pkg, filters = {}) {
    return matchesNormalizedFilters(pkg, normalizeFilters(filters));
  }

  function compareIds(a, b) {
    return String(a.id ?? '').localeCompare(String(b.id ?? ''));
  }

  function fuzzyDistance(term) {
    // Keep short names and punctuation exact: C++, C#, .NET and Node.js identify distinct tools.
    if (!/^\p{L}{4,}$/u.test(term)) return false;
    return term.length >= 6 ? 2 : 1;
  }

  function createEngine(packages) {
    if (typeof MiniSearch !== 'function') throw new Error('Search library did not load');
    let index;

    function getIndex() {
      if (index) return index;
      index = new MiniSearch({
        idField: '_key',
        fields: ['id', 'name', 'moniker'],
        tokenize: tokenizeQuery,
      });
      index.addAll(packages.map((pkg, key) => ({
        _key: key,
        id: String(pkg.id ?? ''),
        name: String(pkg.name ?? ''),
        moniker: String(pkg.moniker ?? ''),
      })));
      return index;
    }

    function search(query, filters = {}) {
      const normalized = normalizeSearchQuery(query);
      const tokens = tokenizeQuery(normalized);
      const constraints = normalizeFilters(filters);
      const constrained = Boolean(constraints.publisher || constraints.tags.length);
      const allowed = pkg => !constrained || matchesNormalizedFilters(pkg, constraints);
      if (!tokens.length) {
        return { results: packages.filter(allowed).sort(compareIds), fuzzy: false };
      }

      const ordinary = packages
        .filter(allowed)
        .map(pkg => ({ pkg, score: scorePackage(pkg, normalized, tokens) }))
        .filter(result => result.score > 0)
        .sort((a, b) => b.score - a.score || compareIds(a.pkg, b.pkg));
      if (ordinary.length || !tokens.some(token => fuzzyDistance(token))) {
        return { results: ordinary.map(result => result.pkg), fuzzy: false };
      }

      const matches = getIndex().search(normalized, {
        combineWith: 'AND',
        fuzzy: fuzzyDistance,
        prefix: false,
        boost: { id: 3, moniker: 3, name: 2 },
        filter: result => allowed(packages[result.id]),
      });
      matches.sort((a, b) => b.score - a.score || compareIds(packages[a.id], packages[b.id]));
      return { results: matches.map(result => packages[result.id]), fuzzy: matches.length > 0 };
    }

    return { search };
  }

  return { normalizeSearchQuery, tokenizeQuery, scorePackage, normalizeFilters, matchesFilters, createEngine };
});
