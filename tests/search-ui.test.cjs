const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const WingetSearch = require('../search.js');
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1];
const catalog = [
  { id: 'A.Editor', name: 'Editor', publisher: 'Acme', tags: ['code', 'tools'] },
  { id: 'B.Editor', name: 'Editor', publisher: 'Other', tags: ['code'] },
  { id: 'C.Editor', name: 'Editor', publisher: 'Acme Labs', tags: ['tools'] },
  { id: 'D.Tool', name: 'Tool', publisher: 'Acme', tags: ['tools'] },
];

function setup(search = '') {
  const elements = new Map();
  const events = {};
  const timers = new Map();
  let nextTimer = 0;
  const stack = [new URL(`https://example.test/winget-search/${search}`)];
  let position = 0;
  const window = { location: stack[0], addEventListener(name, fn) { events[name] = fn; } };
  const history = {
    pushState(_, __, value) {
      stack.splice(++position);
      stack.push(new URL(value, window.location));
      window.location = stack[position];
    },
    replaceState(_, __, value) { window.location = stack[position] = new URL(value, window.location); },
  };
  function element() {
    return {
      value: '', textContent: '', innerHTML: '', style: {}, handlers: {},
      addEventListener(name, fn) { this.handlers[name] = fn; },
      contains() { return true; }, focus() {},
      insertAdjacentHTML(_, value) { this.innerHTML += value; },
    };
  }
  const document = {
    getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); },
    addEventListener(name, fn) { events[name] = fn; },
    createElement() {
      return {
        set textContent(value) { this.innerHTML = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); },
      };
    },
  };
  const context = vm.createContext({
    WingetSearch, window, document, history, URL, URLSearchParams,
    fetch: () => new Promise(() => {}),
    setTimeout(fn) { timers.set(++nextTimer, fn); return nextTimer; },
    clearTimeout(id) { timers.delete(id); },
  });
  vm.runInContext(script, context);
  context.catalog = catalog;
  vm.runInContext('packages = catalog; searchEngine = WingetSearch.createEngine(packages); restoreSearchState();', context);
  return {
    context, elements, window, stack, events,
    flush() { const pending = [...timers.values()]; timers.clear(); pending.forEach(fn => fn()); },
    type(value) { const input = elements.get('search'); input.value = value; input.handlers.input.call(input); },
    go(delta) { position += delta; window.location = stack[position]; events.popstate(); },
    clickChip(dataset) {
      const button = { dataset, hasAttribute: name => name === 'data-clear-filters' && dataset.clear };
      elements.get('active-filters').handlers.click({ target: { closest: () => button } });
    },
    ids() { return Array.from(vm.runInContext('currentResults.map(pkg => pkg.id)', context)); },
  };
}

test('publisher and tag clicks preserve text, enforce fields, and create removable chips', () => {
  const ui = setup('?q=Editor');
  ui.context.filterBy('publisher', 'Acme');
  assert.equal(ui.elements.get('search').value, 'Editor');
  assert.deepEqual(ui.ids(), ['A.Editor']);
  assert.match(ui.elements.get('active-filters').innerHTML, /Remove Publisher: Acme/);
  ui.context.filterBy('tag', 'tools');
  assert.equal(ui.window.location.search, '?q=Editor&publisher=Acme&tag=tools');
  ui.clickChip({ removeFilter: 'publisher', filterValue: 'Acme' });
  assert.deepEqual(ui.ids(), ['A.Editor', 'C.Editor']);
  ui.clickChip({ removeFilter: 'tag', filterValue: 'tools' });
  assert.deepEqual(ui.ids(), ['A.Editor', 'B.Editor', 'C.Editor']);
});

test('filter-only reload restores all constraints and correct totals', () => {
  const ui = setup('?publisher=ACME&tag=tools&tag=code&tag=CODE');
  assert.deepEqual(ui.ids(), ['A.Editor']);
  assert.equal(ui.elements.get('stats').textContent, 'Showing 1 of 1 matches');
  ui.clickChip({ clear: true });
  assert.equal(ui.window.location.search, '');
  assert.match(ui.elements.get('results').innerHTML, /Start with a common package/);
});

test('back and forward restore query and filters and cancel pending input', () => {
  const ui = setup('?q=Editor');
  ui.context.filterBy('publisher', 'Acme');
  ui.context.filterBy('tag', 'tools');
  ui.type('pending text');
  ui.go(-1);
  ui.flush();
  assert.equal(ui.elements.get('search').value, 'Editor');
  assert.equal(ui.window.location.search, '?q=Editor&publisher=Acme');
  ui.go(-1);
  assert.deepEqual(ui.ids(), ['A.Editor', 'B.Editor', 'C.Editor']);
  ui.go(1);
  assert.deepEqual(ui.ids(), ['A.Editor']);
  ui.go(1);
  assert.equal(ui.window.location.search, '?q=Editor&publisher=Acme&tag=tools');
});

test('typing shares one history entry per edit session and retains prior filter state', () => {
  const ui = setup('?q=Editor');
  ui.context.filterBy('publisher', 'Acme');
  ui.type('T'); ui.flush();
  ui.type('Tool'); ui.flush();
  assert.equal(ui.stack.length, 3);
  assert.deepEqual(ui.ids(), ['D.Tool', 'A.Editor']);
  ui.go(-1);
  assert.equal(ui.elements.get('search').value, 'Editor');
  assert.deepEqual(ui.ids(), ['A.Editor']);
});

test('filter action preserves pending query and cancels its debounce', () => {
  const ui = setup('?q=Editor');
  ui.type('Tool');
  ui.context.filterBy('publisher', 'Acme');
  ui.flush();
  assert.equal(ui.window.location.search, '?q=Tool&publisher=Acme');
  assert.deepEqual(ui.ids(), ['D.Tool', 'A.Editor']);
  ui.go(-1);
  assert.equal(ui.window.location.search, '?q=Tool');
});

test('query state round-trips punctuation, escapes chips, and keeps other URL parts', () => {
  const value = 'A&B + C# <img src=x onerror=alert(1)>';
  const ui = setup('?q=C%2B%2B&source=docs#search');
  ui.context.filterBy('publisher', value);
  const restored = ui.context.readSearchState(ui.window.location.search);
  assert.equal(restored.query, 'C++');
  assert.equal(restored.filters.publisher, value);
  assert.equal(ui.window.location.searchParams.get('source'), 'docs');
  assert.equal(ui.window.location.hash, '#search');
  assert.doesNotMatch(ui.elements.get('active-filters').innerHTML, /<img/);
  assert.match(ui.elements.get('active-filters').innerHTML, /&lt;img/);
});

test('filter-only empty state explains how to recover', () => {
  const ui = setup('?publisher=missing');
  assert.equal(ui.elements.get('stats').textContent, '0 matches with these filters');
  assert.match(ui.elements.get('results').innerHTML, /Remove a filter/);
});

test('rendered publisher and tag buttons identify their distinct fields', () => {
  const ui = setup('?q=Editor');
  const rendered = ui.context.renderPackage(catalog[0], 'Editor');
  assert.match(rendered, /data-filter-field="publisher" data-filter-value="Acme"/);
  assert.match(rendered, /data-filter-field="tag" data-filter-value="code"/);
  for (const query of ['C++', 'C#', '.NET', 'Node.js', '(test']) {
    assert.doesNotThrow(() => ui.context.highlightMatch(query, query));
  }
});

test('a pause after a space does not join the next word to the previous word', () => {
  const ui = setup();
  ui.type('Visual '); ui.flush();
  assert.equal(ui.elements.get('search').value, 'Visual ');
  ui.type('Visual Studio'); ui.flush();
  assert.equal(ui.window.location.searchParams.get('q'), 'Visual Studio');
});

test('blurring before debounce preserves the query as a separate history entry', () => {
  const ui = setup('?q=Editor');
  ui.type('Google');
  ui.elements.get('search').handlers.blur();
  ui.flush();
  ui.type('Chrome'); ui.flush();
  assert.deepEqual(ui.stack.map(url => url.searchParams.get('q')), ['Editor', 'Google', 'Chrome']);
});

test('blur leaves rendered filter buttons in place until their click can run', () => {
  const ui = setup('?q=Editor');
  const original = ui.elements.get('results').innerHTML;
  ui.type('Tool');
  ui.elements.get('search').handlers.blur();
  assert.equal(ui.elements.get('results').innerHTML, original);
  ui.context.filterBy('publisher', 'Acme');
  ui.flush();
  assert.equal(ui.window.location.search, '?q=Tool&publisher=Acme');
});
