async (page) => {
  const base = await page.evaluate(() => new URL('.', location.href).href);
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  const ready = async () => {
    await page.locator('#loading').waitFor({ state: 'hidden' });
    check(!await page.locator('#error').isVisible(), 'Catalog must load');
  };
  const landmarks = async label => {
    check(await page.getByRole('banner').count() === 1, `${label}: one page header`);
    check(await page.getByRole('main').count() === 1, `${label}: one main landmark`);
    check(await page.getByRole('contentinfo').count() === 1, `${label}: one footer landmark`);
    check(await page.getByRole('heading', { level: 1 }).count() === 1, `${label}: one primary heading`);
    await page.locator('.skip-link').focus();
    const skip = await page.locator('.skip-link').boundingBox();
    check(skip && skip.y >= 0, `${label}: focused skip link is visible`);
    await page.keyboard.press('Enter');
    check(await page.locator('main').evaluate(el => el === document.activeElement), `${label}: skip link focuses main`);
  };
  const noOverflow = async label => {
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${label}: no horizontal overflow`);
  };
  const decorativeIcons = async label => {
    check(await page.locator('svg:not([aria-hidden="true"]), svg:not([focusable="false"])').count() === 0,
      `${label}: decorative icons stay out of the accessibility tree and tab order`);
  };
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], {
    origin: await page.evaluate(() => location.origin),
  });
  await page.goto(base);
  await ready();
  const metadata = await page.evaluate(async () => {
    const source = new DOMParser().parseFromString(await (await fetch('.')).text(), 'text/html');
    const catalog = await (await fetch('packages.json')).json();
    const json = JSON.parse(source.querySelector('script[type="application/ld+json"]').textContent);
    const meta = name => source.querySelector(`meta[property="${name}"], meta[name="${name}"]`)?.content;
    return {
      canonical: source.querySelector('link[rel="canonical"]').href,
      title: source.title,
      description: meta('description'),
      ogTitle: meta('og:title'), ogDescription: meta('og:description'), ogUrl: meta('og:url'),
      twitterTitle: meta('twitter:title'), twitterDescription: meta('twitter:description'),
      image: meta('og:image'), twitterImage: meta('twitter:image'), imageAlt: meta('og:image:alt'),
      summary: source.querySelector('#catalog-summary').textContent,
      summaryTime: source.querySelector('#catalog-summary time')?.dateTime,
      json, actualCount: catalog.packages.length, total: catalog.metadata.total,
      extractedAt: catalog.metadata.extracted_at,
    };
  });
  const publicUrls = await page.evaluate(value => {
    const canonical = new URL(value);
    return { valid: canonical.protocol === 'https:' && !canonical.search && !canonical.hash,
      image: new URL('og-image.png', canonical).href, catalog: new URL('packages.json', canonical).href,
      agent: new URL('agent-access.html', canonical).href };
  }, metadata.canonical);
  check(publicUrls.valid, 'Public canonical uses HTTPS with no filters or fragment');
  check(metadata.ogUrl === metadata.canonical && metadata.json.url === metadata.canonical, 'Canonical, Open Graph and Dataset agree');
  check(metadata.title === metadata.ogTitle && metadata.title === metadata.twitterTitle, 'Social titles match the page title');
  check(metadata.description === metadata.ogDescription && metadata.description === metadata.twitterDescription, 'Social descriptions match the page description');
  check(metadata.image === publicUrls.image && metadata.twitterImage === metadata.image,
    'Social preview URLs share the public base');
  check(Boolean(metadata.imageAlt), 'Preview image has descriptive alternative text');
  check(metadata.json.distribution.contentUrl === publicUrls.catalog, 'Dataset points to the public catalog');
  check(metadata.actualCount === metadata.total, 'Catalog count equals metadata total');
  check(!('numberOfItems' in metadata.json), 'Dataset omits the ItemList-only count property');
  check(JSON.stringify(metadata.json.variableMeasured) === JSON.stringify(['id', 'name', 'version', 'publisher']), 'Dataset fields match package records');
  check(metadata.summary.startsWith(metadata.json.description), 'Structured description matches visible content before JavaScript runs');
  check(metadata.summary.replaceAll(',', '').includes(String(metadata.actualCount)), 'Visible catalog summary has the actual count');
  const extractionTime = Date.parse(/(?:Z|[+-]\d\d:\d\d)$/.test(metadata.extractedAt) ? metadata.extractedAt : `${metadata.extractedAt}Z`);
  check(Date.parse(metadata.json.dateModified) === extractionTime, 'Dataset date uses catalog extraction time');
  check(Date.parse(metadata.summaryTime) === extractionTime, 'Visible catalog freshness uses the extraction time');

  const reports = [];
  for (const width of [1280, 375]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(base);
    await ready();
    await landmarks(`${width}: homepage`);
    await page.keyboard.press('Tab');
    check(await page.locator('#search').evaluate(el => el === document.activeElement), 'Search follows the main skip target in keyboard order');
    await noOverflow(`${width}: homepage`);
    await page.locator('#search').fill('vscode');
    await page.waitForFunction(() => currentQuery === 'vscode');
    check(await page.locator('.pkg').count() > 0, 'Search displays packages');
    check(await page.locator('.pkg h2.pkg-name').count() === await page.locator('.pkg').count(), 'Every package has a level-two result heading');
    check(await page.locator('.pkg-id').first().textContent() === 'Microsoft.VisualStudioCode', 'Result heading change preserves ranking');
    await decorativeIcons('Search results');
    await page.locator('.copy-btn').first().focus();
    await page.keyboard.press('Enter');
    await page.locator('.copy-btn.success').first().waitFor();
    await decorativeIcons('Copied state');
    check(await page.evaluate(() => navigator.clipboard.readText()) === 'winget install -e --id Microsoft.VisualStudioCode', 'Keyboard copy preserves command');
    await page.locator('.pkg details summary').first().focus();
    await page.keyboard.press('Enter');
    check(await page.locator('.pkg details').first().evaluate(el => el.open), 'Keyboard opens package details');
    await noOverflow(`${width}: expanded result`);
    check(await page.locator('.command').evaluateAll(elements => elements.every(el => el.scrollWidth <= el.clientWidth)),
      'Install commands wrap so the whole command is visible without horizontal scrolling');
    await page.screenshot({ path: `.playwright-cli/winget-seo-${width}.png` });
    await page.goto(`${base}?q=vscode&publisher=Microsoft&tag=code`);
    await ready();
    check(await page.locator('link[rel="canonical"]').getAttribute('href') === metadata.canonical, 'Query and filter URLs retain the root canonical');

    await page.goto(`${base}agent-access.html`);
    await landmarks(`${width}: agent instructions`);
    check(await page.locator('link[rel="canonical"]').getAttribute('href') === publicUrls.agent,
      'Agent instructions use their own public canonical');
    check(await page.getByRole('heading', { level: 2 }).count() === 4, 'Agent instructions retain all sections');
    await noOverflow(`${width}: agent instructions`);
    for (const example of await page.locator('pre').all()) {
      await example.focus();
      check(await example.evaluate(el => el === document.activeElement), 'Code examples accept keyboard focus');
      if (await example.evaluate(el => el.scrollWidth > el.clientWidth)) {
        await example.evaluate(el => { el.scrollLeft = 0; });
        await page.keyboard.press('ArrowRight');
        await page.waitForFunction(() => document.activeElement.scrollLeft > 0);
      }
    }
    await page.screenshot({ path: `.playwright-cli/winget-agent-seo-${width}.png` });
    reports.push({ width, passed: true });
  }
  await page.goto(base);
  await ready();
  check(failures.length === 0, `Browser exceptions: ${failures.join('; ')}`);
  return { reports, catalogCount: metadata.actualCount, canonical: metadata.canonical, exceptions: failures };
}
