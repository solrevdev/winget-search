const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const { createEngine, matchesFilters, normalizeFilters } = require('../search.js');

const vscode = {
  id: 'Microsoft.VisualStudioCode', name: 'Microsoft Visual Studio Code',
  moniker: 'vscode', publisher: 'Microsoft Corporation', tags: ['editor', 'developer-tools'],
};
const chrome = { id: 'Google.Chrome', name: 'Google Chrome', publisher: 'Google LLC', tags: ['browser'] };
const packages = [
  { ...vscode, id: 'Microsoft.VisualStudioCode.Insiders', name: 'Microsoft Visual Studio Code Insiders', moniker: 'vscode-insiders' },
  vscode, chrome,
  { ...chrome, id: 'Google.Chrome.Beta', name: 'Google Chrome Beta' },
];

test('transposed words find the standard desktop package before variants', () => {
  const engine = createEngine(packages);
  for (const [query, id] of [['visaul studio code', vscode.id], ['googel chrome', chrome.id]]) {
    const result = engine.search(query);
    assert.equal(result.fuzzy, true);
    assert.equal(result.results[0].id, id);
  }
});

test('ordinary monikers, aliases and exact names retain their order', () => {
  const engine = createEngine(packages);
  for (const query of ['vscode', 'vs code', ' VS   Code ', 'Visual Studio Code']) {
    const result = engine.search(query);
    assert.equal(result.fuzzy, false);
    assert.equal(result.results[0].id, vscode.id);
  }
});

test('an ordinary description match suppresses fuzzy fallback', () => {
  const literal = { id: 'Test.Literal', description: 'Explains visaul studio code' };
  const result = createEngine([...packages, literal]).search('visaul studio code');
  assert.equal(result.fuzzy, false);
  assert.deepEqual(result.results, [literal]);
});

test('fallback requires every word and indexes only identity fields', () => {
  const engine = createEngine([
    ...packages,
    { id: 'Test.Other', description: 'Google Chrome', publisher: 'Google Chrome', tags: ['Google Chrome'] },
  ]);
  assert.deepEqual(engine.search('googel chrome').results.map(pkg => pkg.id), ['Google.Chrome', 'Google.Chrome.Beta']);
  assert.deepEqual(engine.search('googel chrome zebra').results, []);
});

test('publisher and tag constraints match whole case-insensitive field values', () => {
  assert.equal(matchesFilters(vscode, { publisher: ' MICROSOFT CORPORATION ', tags: ['EDITOR'] }), true);
  for (const filters of [
    { publisher: 'Microsoft' }, { publisher: 'editor' }, { tags: ['edit'] },
    { tags: ['Microsoft Corporation'] }, { tags: ['editor', 'missing'] },
  ]) assert.equal(matchesFilters(vscode, filters), false);
  assert.equal(matchesFilters(vscode, { tags: ['editor', 'developer-tools'] }), true);
});

test('normalization trims, deduplicates tags and ignores malformed values', () => {
  assert.deepEqual(normalizeFilters({ publisher: ' Microsoft ', tags: [' editor ', 'EDITOR', '', null, 12, 'tools'] }), {
    publisher: 'Microsoft', tags: ['editor', 'tools'],
  });
  assert.deepEqual(normalizeFilters(null), { publisher: '', tags: [] });
  assert.deepEqual(normalizeFilters({ publisher: false, tags: 'editor' }), { publisher: '', tags: [] });
});

test('missing metadata and non-string monikers cannot stop a fallback', () => {
  const engine = createEngine([{}, { id: 'Test.Numeric', moniker: 123, tags: [null, 12] }, chrome]);
  assert.equal(engine.search('googel chrome').results[0], chrome);
  assert.deepEqual(engine.search('', { tags: ['browser'] }).results, [chrome]);
  assert.deepEqual(engine.search('', { publisher: 'missing' }).results, []);
});

test('filter-only results sort by ID without mutating the catalog', () => {
  const originalOrder = packages.slice();
  const result = createEngine(packages).search('', { tags: ['editor', 'developer-tools'] });
  assert.equal(result.fuzzy, false);
  assert.deepEqual(result.results.map(pkg => pkg.id), ['Microsoft.VisualStudioCode', 'Microsoft.VisualStudioCode.Insiders']);
  assert.deepEqual(packages, originalOrder);
});

test('filters apply before ordinary matching and also constrain fallback', () => {
  const literal = { id: 'Test.Literal', name: 'visaul studio code', publisher: 'Other' };
  const engine = createEngine([...packages, literal]);
  const result = engine.search('visaul studio code', { publisher: 'Microsoft Corporation', tags: ['editor'] });
  assert.equal(result.fuzzy, true);
  assert.equal(result.results[0], vscode);
  assert.equal(result.results.includes(literal), false);
  assert.deepEqual(engine.search('googel chrome', { publisher: 'Microsoft Corporation' }).results, []);
});

test('fuzzy matching preserves punctuation and short terms in mixed queries', () => {
  const engine = createEngine(['C++', 'C#', '.NET', 'Node.js'].map((name, i) => ({ id: `Test.${i}`, name: `${name} editor` })));
  for (const name of ['C++', 'C#', '.NET', 'Node.js']) {
    const result = engine.search(`${name} editro`);
    assert.equal(result.fuzzy, true);
    assert.deepEqual(result.results.map(pkg => pkg.name), [`${name} editor`]);
  }
  for (const query of ['C editro', 'C+ editro', 'NET editro', 'Node,js editro', 'Node.j editro']) {
    assert.deepEqual(engine.search(query).results, []);
  }
});

test('unknown short or punctuation-only terms do not receive fuzzy matches', () => {
  const engine = createEngine([{ id: 'Test.Ripgrep', moniker: 'rg' }, { id: 'Test.DotNet', name: '.NET' }]);
  for (const query of ['rx', '.NX', 'C++']) {
    const result = engine.search(query);
    assert.deepEqual(result, { results: [], fuzzy: false });
  }
});

test('locally served scripts expose the browser API without CommonJS', () => {
  const context = vm.createContext({});
  for (const file of ['vendor/minisearch-7.2.0.js', 'search.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname, '..', file), 'utf8'), context);
  }
  const result = context.WingetSearch.createEngine(packages).search('googel chrome');
  assert.equal(result.fuzzy, true);
  assert.equal(result.results[0].id, chrome.id);
});

test('a missing search asset fails during initialization rather than the first typo', () => {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'search.js'), 'utf8'), context);
  assert.throws(() => context.WingetSearch.createEngine(packages), /Search library did not load/);
});
