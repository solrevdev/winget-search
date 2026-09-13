const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const elements = new Map();
const context = vm.createContext({
  document: {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { textContent: '', addEventListener() {} });
      return elements.get(id);
    },
    addEventListener() {},
  },
  window: { addEventListener() {} },
  fetch: () => new Promise(() => {}),
});
vm.runInContext(script, context);

function ranked(query, packages) {
  const normalized = context.normalizeSearchQuery(query);
  const tokens = context.tokenizeQuery(normalized);
  return packages
    .map(pkg => ({ id: pkg.id, score: context.scorePackage(pkg, normalized, tokens) }))
    .filter(result => result.score > 0)
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id))
    .map(result => result.id);
}

const vscode = {
  id: 'Microsoft.VisualStudioCode',
  name: 'Microsoft Visual Studio Code',
  moniker: 'vscode',
  publisher: 'Microsoft Corporation',
  shortDescription: 'A code editor for modern web and cloud applications.',
  tags: ['developer-tools', 'editor'],
};
const packages = [
  { id: 'Example.WorkspaceLauncherForVSCode', name: 'Visual Studio / Code for Command Palette', tags: ['vscode'] },
  { ...vscode, id: 'Microsoft.VisualStudioCode.Insiders', name: 'Microsoft Visual Studio Code Insiders', moniker: 'vscode-insiders' },
  vscode,
  { id: 'Other.Editor', name: 'Another editor', description: 'Works with Visual Studio Code and vscode.' },
];

for (const query of ['Visual Studio Code', 'vscode', 'vs code', ' VS   Code ', 'MICROSOFT.VISUALSTUDIOCODE']) {
  test(`${JSON.stringify(query)} puts the standard VS Code package first`, () => {
    assert.equal(ranked(query, packages)[0], vscode.id);
  });
}

test('an exact ID wins even when another package uses it as a moniker', () => {
  assert.equal(ranked(vscode.id, [
    { id: 'Other.Package', name: vscode.id, moniker: vscode.id, tags: [vscode.id] }, vscode,
  ])[0], vscode.id);
});

test('monikers work for packages outside the alias map', () => {
  assert.equal(ranked('rg', [
    { id: 'Example.rgHelper', name: 'rg helper' },
    { id: 'BurntSushi.ripgrep.MSVC', name: 'ripgrep', moniker: 'rg' },
  ])[0], 'BurntSushi.ripgrep.MSVC');
});

test('a non-string moniker cannot stop the search', () => {
  assert.equal(ranked('tool', [
    { id: 'Example.Numeric', moniker: 123 },
    { id: 'Example.Boolean', moniker: true },
    { id: 'Example.Tool', moniker: 'tool' },
  ])[0], 'Example.Tool');
});

test('the exact 7-Zip name beats forks with more matching fields', () => {
  assert.equal(ranked('7-Zip', [
    { id: 'mcmilk.7zip-zstd', name: '7-Zip ZS', publisher: '7-Zip', description: '7-Zip fork', tags: ['7-Zip'] },
    { id: '7zip.7zip', name: '7-Zip', moniker: '7zip' },
  ])[0], '7zip.7zip');
});

test('description and shortDescription are both searchable', () => {
  const pkg = { id: 'Test.Editor', shortDescription: 'Small editor', description: 'Supports large files' };
  assert.deepEqual(ranked('small', [pkg]), [pkg.id]);
  assert.deepEqual(ranked('large files', [pkg]), [pkg.id]);
});

test('all words must match and absent optional fields are allowed', () => {
  const pkg = { id: 'Test.Tool', tags: [null, 12, 'utility'] };
  assert.deepEqual(ranked('test utility', [pkg]), [pkg.id]);
  assert.deepEqual(ranked('test missing', [pkg]), []);
  assert.deepEqual(ranked('nothing', [{}]), []);
});

test('punctuation keeps C++, C#, .NET, and Node.js distinct', () => {
  for (const name of ['C++', 'C#', '.NET', 'Node.js', '(test', 'foo+bar']) {
    const pkg = { id: `Test.${name}`, name };
    assert.equal(ranked(name, [{ id: 'Other', name: 'Unrelated' }, pkg])[0], pkg.id);
  }
  assert.deepEqual(ranked('C++', [{ id: 'Test.CSharp', name: 'C#' }]), []);
});

test('ordinary paging shows the actual total without the 200-result limit', () => {
  context.updateStats('Visual Studio Code', 27, 25);
  assert.equal(elements.get('stats').textContent, 'Showing 25 of 27 matches');
  context.updateStats('Visual Studio Code', 27, 27);
  assert.equal(elements.get('stats').textContent, 'Showing 27 of 27 matches');
});

test('the cap is mentioned only when there are more than 200 matches', () => {
  context.updateStats('git', 822, 25);
  assert.match(elements.get('stats').textContent, /^Showing 25 of 822 matches • limited to the top 200/);
  context.updateStats('editor', 200, 25);
  assert.equal(elements.get('stats').textContent, 'Showing 25 of 200 matches');
  context.updateStats('missing', 0, 0);
  assert.equal(elements.get('stats').textContent, '0 matches for "missing"');
});
