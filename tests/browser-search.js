async (page) => {
  const base = await page.evaluate(() => new URL('.', location.href).href);
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  const ready = async () => {
    await page.locator('#loading').waitFor({ state: 'hidden' });
    check(!await page.locator('#error').isVisible(), 'Catalog must load');
  };
  const search = async query => {
    await page.locator('#search').fill(query);
    await page.waitForFunction(q => currentQuery === q, query);
  };
  const urlParam = name => page.evaluate(key => new URL(location.href).searchParams.get(key), name);
  const firstId = () => page.locator('.pkg-id').first().textContent();
  const verifyConstraints = () => page.evaluate(() => currentResults.length > 0 &&
    currentResults.every(pkg => WingetSearch.matchesFilters(pkg, activeFilters)));
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: await page.evaluate(() => location.origin) });
  const reports = [];
  for (const width of [1280, 375]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(base);
    await ready();
    for (const [query, id] of [
      ['vscode', 'Microsoft.VisualStudioCode'], ['vs code', 'Microsoft.VisualStudioCode'],
      ['Visual Studio Code', 'Microsoft.VisualStudioCode'], ['7-Zip', '7zip.7zip'],
      ['7zip', '7zip.7zip'], ['visaul studio code', 'Microsoft.VisualStudioCode'],
      ['googel chrome', 'Google.Chrome'],
    ]) {
      await search(query);
      check(await firstId() === id, `${width}: ${query} ranking`);
    }
    check((await page.locator('#search-note').textContent()).includes('similar'), 'Explain fuzzy results');
    for (const query of ['C++', 'C#', '.NET', 'Node.js', '(test']) {
      await search(query);
      check(await page.locator('.pkg').count() > 0, `${width}: ${query} results`);
    }
    await search('vscode');
    const unfiltered = await page.evaluate(() => lastMatchCount);
    await page.locator('.copy-btn').first().click();
    await page.locator('.copy-btn').first().filter({ hasText: 'Copied!' }).waitFor();
    check(await page.evaluate(() => navigator.clipboard.readText()) === 'winget install -e --id Microsoft.VisualStudioCode', 'Clipboard command');
    await page.locator('.pkg details summary').first().click();
    const publisher = await page.locator('.pkg').first().locator('[data-filter-field="publisher"]').textContent();
    const tag = await page.locator('.pkg').first().locator('[data-filter-field="tag"]').first().textContent();
    await page.locator('.pkg').first().locator('[data-filter-field="publisher"]').click();
    check(await page.locator('#search').inputValue() === 'vscode', 'Publisher retains query');
    check(await verifyConstraints(), 'Publisher excludes other fields');
    await page.locator('.pkg details summary').first().click();
    await page.locator('.pkg').first().locator('[data-filter-field="tag"]').first().click();
    check(await verifyConstraints(), 'Combined constraints');
    check(await urlParam('tag') === tag, 'Tag URL');
    await page.reload(); await ready();
    check(await verifyConstraints(), 'Reload constraints');
    check(await page.locator('.filter-chip').count() === 2, 'Reload chips');
    await page.goBack();
    await page.waitForFunction(() => activeFilters.tags.length === 0);
    check(await urlParam('publisher') === publisher, 'Back retains publisher');
    await page.goForward();
    await page.waitForFunction(() => activeFilters.tags.length === 1);
    await page.getByRole('button', { name: `Remove Publisher: ${publisher}`, exact: true }).click();
    check(await verifyConstraints(), 'Tag-only removal constraints');
    await page.getByRole('button', { name: 'Clear filters', exact: true }).click();
    check(await page.evaluate(() => lastMatchCount) === unfiltered, 'Clearing restores results');

    await page.goto(`${base}?publisher=${encodeURIComponent(publisher)}&tag=${encodeURIComponent(tag)}`);
    await ready();
    check(await verifyConstraints(), 'Filter-only URL');
    check(!(await page.locator('#stats').textContent()).includes('try a common'), 'Filter-only totals');
    await page.locator('#search').focus();
    await page.keyboard.press('Escape');
    check(await page.locator('.filter-chip').count() === 2, 'Escape preserves filters');
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'No horizontal overflow');
    await page.screenshot({ path: `.playwright-cli/winget-search-${width}.png` });
    await page.getByRole('button', { name: 'Clear filters', exact: true }).click();
    await page.locator('body').click({ position: { x: 5, y: 5 } });
    await page.keyboard.press('/');
    check(await page.locator('#search').evaluate(el => el === document.activeElement), 'Slash focuses search');
    await search('git');
    check(await page.locator('.pkg').count() === 25, 'First page size');
    await page.getByRole('button', { name: /Load more/ }).click();
    check(await page.locator('.pkg').count() === 50, 'Second page size');
    check((await page.locator('#stats').textContent()).includes('limited to the top 200'), 'Cap warning');
    await search('zzzzzzzzqqqqqqqq');
    check(await page.locator('.no-results').isVisible(), 'No matches state');
    await page.goto(`${base}?publisher=NoSuchPublisher987`); await ready();
    check((await page.locator('.no-results').textContent()).includes('Remove a filter'), 'Filtered no matches recovery');
    reports.push({ width, passed: true });
  }
  await page.route('**/packages.json', route => route.fulfill({ status: 503, body: 'Unavailable' }));
  await page.reload();
  await page.locator('#error').waitFor({ state: 'visible' });
  check((await page.locator('#error').textContent()).includes('Failed to load'), 'Catalog error');
  await page.unroute('**/packages.json');
  await page.route('**/packages.json', route => route.fulfill({ json: { packages: [], metadata: { total: 0 } } }));
  await page.goto(base); await ready();
  check((await page.locator('#stats').textContent()).startsWith('0 packages'), 'Empty catalog');
  await page.unroute('**/packages.json');
  await page.route('**/vendor/minisearch-7.2.0.js', route => route.abort());
  await page.goto(base);
  await page.locator('#error').waitFor({ state: 'visible' });
  check(await page.locator('#search').isDisabled(), 'Missing search asset keeps input disabled');
  await page.unroute('**/vendor/minisearch-7.2.0.js');
  await page.goto(`${base}?q=visaul+studio+code`); await ready();
  check(await firstId() === 'Microsoft.VisualStudioCode', 'Initial typo URL');
  check(failures.length === 0, `Browser exceptions: ${failures.join('; ')}`);
  return { reports, exceptions: failures };
}
