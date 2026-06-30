const grid = document.getElementById('grid');
const summary = document.getElementById('summary');
const searchInput = document.getElementById('search');
const presetFilter = document.getElementById('presetFilter');
const storeFilter = document.getElementById('storeFilter');
const themeFilter = document.getElementById('themeFilter');
const topN = document.getElementById('topN');
const sortBy = document.getElementById('sortBy');

let allSets = [];

function decodeHtmlEntities(text) {
  const value = String(text || '');
  const parser = new DOMParser();
  return parser.parseFromString(value, 'text/html').documentElement.textContent || value;
}

function toNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function formatFixed(value, digits) {
  const num = toNumber(value);
  return num === null ? '-' : num.toFixed(digits);
}

function cardTemplate(item) {
  const imageUrl = item.display_image_url || item.bricklink_image_url || item.img_url || '';
  const STORES = [
    { key: 'coolshop_price',   label: 'Coolshop' },
    { key: 'kubbabudin_price', label: 'Kubbabudin' },
    { key: 'boozt_price',      label: 'Boozt' },
    { key: 'hagkaup_price',    label: 'Hagkaup' },
    { key: 'kidsworld_price',  label: 'Kidsworld' },
    { key: 'elko_price',       label: 'Elko' },
  ];
  const storeUrlKey = `${item.lowest_price_store || ''}_url`;
  const fallbackSearchByStore = {
    coolshop: `https://www.coolshop.is/search?query=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
    kubbabudin: `https://kubbabudin.is/leita/?q=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
    boozt: `https://www.boozt.com/is/is/search?q=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
    hagkaup: `https://www.hagkaup.is/search?q=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
    kidsworld: `https://www.kids-world.com/is-is/search?q=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
    elko: `https://elko.is/leit?q=${encodeURIComponent(item.lego_set_number || item.name || '')}`,
  };
  const productUrl = item[storeUrlKey] || fallbackSearchByStore[item.lowest_price_store] || null;
  const storeRows = STORES
    .filter(s => item[s.key])
    .map(s => `<div class="store-row"><span class="label">${s.label}:</span> <span class="value">${item[s.key]}</span></div>`)
    .join('');
  return `
    <article class="card">
      ${imageUrl ? `<img class="thumb" src="${imageUrl}" alt="${item.lego_set_number} image" loading="lazy" />` : ''}
      <h3>${item.lego_set_number} — ${item.name || 'Unknown'}</h3>
      ${productUrl ? `<a class="product-link" href="${productUrl}" target="_blank" rel="noopener noreferrer">View product ↗</a>` : ''}
      <div class="meta">
        <div><span class="label">Theme:</span> <span class="value">${decodeHtmlEntities(item.theme || '-')}</span></div>
        <div><span class="label">Pieces:</span> <span class="value">${item.num_parts || '-'}</span></div>
        <div class="best-price"><span class="label">Best price:</span> <span class="value">${item.lowest_price || '-'} @ ${item.lowest_price_store || '-'}</span></div>
        <div><span class="label">Pieces/ISK:</span> <span class="value">${formatFixed(item.pieces_per_kr, 4)}</span></div>
        <div><span class="label">BrickLink avg (ISK incl. VAT):</span> <span class="value">${toNumber(item.bricklink_6m_avg_price_new_isk) != null ? Math.round(toNumber(item.bricklink_6m_avg_price_new_isk) * 1.24) + ' kr' : '-'}</span></div>
        <div><span class="label">Price vs BL avg ratio:</span> <span class="value">${toNumber(item.lowest_price_vs_bricklink_avg_ratio)?.toFixed(3) ?? '-'}</span></div>
        <div><span class="label">BrickLink sales:</span> <span class="value">${item.bricklink_6m_sales_count_new ?? '-'}</span></div>
      </div>
      ${storeRows ? `<details class="store-prices"><summary>Store prices (${STORES.filter(s => item[s.key]).length})</summary><div class="store-grid">${storeRows}</div></details>` : ''}
    </article>
  `;
}

function countStorePrices(item) {
  return ['coolshop_price', 'kubbabudin_price', 'boozt_price', 'hagkaup_price', 'kidsworld_price', 'elko_price']
    .filter((key) => Boolean(item[key])).length;
}

function passesPreset(item, preset) {
  if (preset === 'strictValue') {
    return countStorePrices(item) >= 2 && Number(item.num_parts || 0) > 0;
  }
  if (preset === 'bricklinkLiquid') {
    return (toNumber(item.bricklink_6m_sales_count_new) || 0) >= 10;
  }
  return true;
}

function filterAndSort() {
  const q = searchInput.value.trim().toLowerCase();
  const preset = presetFilter.value;
  const store = storeFilter.value;
  const theme = themeFilter.value;
  const limit = topN.value;
  const sort = sortBy.value;

  let rows = allSets.filter((item) => {
    const matchesQuery = !q ||
      String(item.lego_set_number || '').toLowerCase().includes(q) ||
      String(item.name || '').toLowerCase().includes(q);

    const matchesStore = store === 'all' || Boolean(item[`${store}_price`]);
    const itemTheme = decodeHtmlEntities(String(item.theme || '').trim());
    const matchesTheme = theme === 'all' || itemTheme === theme;
    return matchesQuery && matchesStore && matchesTheme && passesPreset(item, preset);
  });

  rows.sort((a, b) => {
    if (sort === 'value') return (b.pieces_per_kr || 0) - (a.pieces_per_kr || 0);
    if (sort === 'priceAsc') return (a.lowest_price_isk || Infinity) - (b.lowest_price_isk || Infinity);
    if (sort === 'priceDesc') return (b.lowest_price_isk || 0) - (a.lowest_price_isk || 0);
    if (sort === 'ratioAsc') return (toNumber(a.lowest_price_vs_bricklink_avg_ratio) || Infinity) - (toNumber(b.lowest_price_vs_bricklink_avg_ratio) || Infinity);
    if (sort === 'bricklinkAvg') return (toNumber(a.bricklink_6m_avg_price_new_usd) || Infinity) - (toNumber(b.bricklink_6m_avg_price_new_usd) || Infinity);
    if (sort === 'bricklinkSales') return (toNumber(b.bricklink_6m_sales_count_new) || 0) - (toNumber(a.bricklink_6m_sales_count_new) || 0);
    return 0;
  });

  const fullCount = rows.length;
  if (limit !== 'all') {
    rows = rows.slice(0, Number(limit));
  }

  summary.textContent = `Showing ${rows.length} of ${fullCount} sets`;
  grid.innerHTML = rows.map(cardTemplate).join('');
}

function populateThemeFilter(rows) {
  const themes = Array.from(
    new Set(
      rows
        .map((item) => decodeHtmlEntities(String(item.theme || '').trim()))
        .filter(Boolean)
    )
  ).sort((a, b) => a.localeCompare(b));

  themeFilter.innerHTML = '<option value="all">All themes</option>';
  for (const themeName of themes) {
    const option = document.createElement('option');
    option.value = themeName;
    option.textContent = themeName;
    themeFilter.appendChild(option);
  }
}

async function loadData() {
  const candidates = ['../data/aggregated_products.json', './data/aggregated_products.json', '/data/aggregated_products.json'];
  let data = null;

  for (const path of candidates) {
    try {
      const res = await fetch(path);
      if (res.ok) {
        data = await res.json();
        break;
      }
    } catch (_) {
      // try next candidate
    }
  }

  if (!data) {
    summary.textContent = 'Could not load aggregated_products.json. Serve workspace with: python -m http.server 8000';
    return;
  }

  allSets = data;
  populateThemeFilter(allSets);
  filterAndSort();
}

searchInput.addEventListener('input', filterAndSort);
presetFilter.addEventListener('change', filterAndSort);
storeFilter.addEventListener('change', filterAndSort);
themeFilter.addEventListener('change', filterAndSort);
topN.addEventListener('change', filterAndSort);
sortBy.addEventListener('change', filterAndSort);

loadData();
