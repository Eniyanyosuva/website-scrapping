/* ============================================================
   AI Shopping Assistant — app.js
   All client-side logic: form, API calls, rendering
   ============================================================ */

'use strict';

const API = {
  SEARCH:   '/api/search',
  PRODUCTS: '/api/products',
  HEALTH:   '/health',
};

// ── DOM refs ─────────────────────────────────────────────────
const form         = document.getElementById('search-form');
const searchBtn    = document.getElementById('search-btn');
const resultsGrid  = document.getElementById('results-grid');
const resultsSection = document.getElementById('results-section');
const resultCountBadge = document.getElementById('result-count');
const statusBar    = document.getElementById('status-bar');
const sbStore      = document.getElementById('sb-store');
const sbCrawled    = document.getElementById('sb-crawled');
const sbMatched    = document.getElementById('sb-matched');
const sbTime       = document.getElementById('sb-time');
const cachedContainer = document.getElementById('cached-container');
const loadCachedBtn  = document.getElementById('load-cached-btn');
const healthDot    = document.getElementById('health-dot');
const toastEl      = document.getElementById('toast');

// ── Health check ─────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(API.HEALTH);
    const data = await res.json();
    healthDot.className = `health-dot ${data.database === 'connected' ? 'ok' : 'error'}`;
    healthDot.title = `Backend ${data.status} | DB: ${data.database}`;
  } catch {
    healthDot.className = 'health-dot error';
    healthDot.title = 'Backend unreachable';
  }
}
checkHealth();

// ── Toast ────────────────────────────────────────────────────
let _toastTimer = null;
function showToast(msg, type = 'info') {
  toastEl.textContent = msg;
  toastEl.className = `toast show ${type}`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toastEl.classList.remove('show'), 3500);
}

// ── Search form submission ────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    shopify_store_url: document.getElementById('store_url').value.trim(),
    product_name:      document.getElementById('product_name').value.trim(),
    occasion:          document.getElementById('occasion').value.trim() || null,
    budget_min:        parseFloat(document.getElementById('budget_min').value) || null,
    budget_max:        parseFloat(document.getElementById('budget_max').value) || null,
    preferences:       document.getElementById('pref_input').value
                         .split(',').map(s => s.trim()).filter(Boolean),
    limit:             parseInt(document.getElementById('result_limit').value, 10),
  };

  if (!payload.shopify_store_url || !payload.product_name) {
    showToast('Store URL and product name are required.', 'danger');
    return;
  }

  setLoading(true);
  resultsSection.hidden = true;
  statusBar.hidden = true;
  resultsGrid.innerHTML = '';

  const t0 = Date.now();

  try {
    const res = await fetch(API.SEARCH, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Search failed');
    }

    const data = await res.json();
    const elapsed = ((Date.now() - t0) / 1000).toFixed(1);

    renderStatusBar(data, elapsed);
    renderResults(data.results);
    showToast(`✅ Found ${data.results.length} matches in ${elapsed}s`, 'success');
  } catch (err) {
    showToast(`❌ ${err.message}`, 'danger');
    resultsGrid.innerHTML = `<div class="error-state">⚠️ ${err.message}</div>`;
    resultsSection.hidden = false;
  } finally {
    setLoading(false);
  }
});

// ── Loading state ─────────────────────────────────────────────
function setLoading(on) {
  searchBtn.classList.toggle('loading', on);
  searchBtn.disabled = on;
  searchBtn.querySelector('.btn-loader').hidden = !on;
}

// ── Status bar ────────────────────────────────────────────────
function renderStatusBar(data, elapsed) {
  const domain = (() => {
    try { return new URL(data.store).hostname; }
    catch { return data.store; }
  })();

  sbStore.textContent   = `🏪 ${domain}`;
  sbCrawled.textContent = `🕷️ ${data.total_crawled} crawled`;
  sbMatched.textContent = `✅ ${data.total_matched} matched`;
  sbTime.textContent    = `⏱ ${elapsed}s`;
  statusBar.hidden = false;
}

// ── Results grid ──────────────────────────────────────────────
function renderResults(products) {
  resultsSection.hidden = false;

  if (!products || products.length === 0) {
    resultCountBadge.textContent = '0 results';
    resultsGrid.innerHTML = '<div class="empty-state">🔍 No matching products found. Try a different query.</div>';
    return;
  }

  resultCountBadge.textContent = `${products.length} result${products.length !== 1 ? 's' : ''}`;
  resultsGrid.innerHTML = products.map((p, i) => buildProductCard(p, i + 1)).join('');
}

function buildProductCard(p, rank) {
  const price = formatPrice(p.price_min, p.price_max, p.currency);
  const score = p.rank_score ?? 0;
  const pct   = Math.min(100, Math.round((score / 100) * 100));

  const imgHtml = p.image_url
    ? `<img src="${esc(p.image_url)}" alt="${esc(p.title)}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=&quot;product-image-placeholder&quot;>🛍️</div>'" />`
    : `<div class="product-image-placeholder">🛍️</div>`;

  const availClass = p.available === 'true' ? 'avail-true' : p.available === 'false' ? 'avail-false' : '';
  const availText  = p.available === 'true' ? 'In Stock' : p.available === 'false' ? 'Out of Stock' : '';
  const availBadge = availClass ? `<span class="avail-badge ${availClass}">${availText}</span>` : '';

  const tags = (p.tags || []).slice(0, 4)
    .map(t => `<span class="tag-pill">${esc(t)}</span>`).join('');

  const visitUrl = p.product_url || p.store_url;

  return `
    <article class="product-card" id="prod-${p.id}">
      <div class="product-image-wrap">
        ${imgHtml}
        <span class="rank-badge">#${rank}</span>
        ${availBadge}
      </div>
      <div class="product-body">
        ${p.vendor ? `<div class="product-vendor">${esc(p.vendor)}</div>` : ''}
        <div class="product-title">${esc(p.title)}</div>
        ${p.product_type ? `<div class="product-type">${esc(p.product_type)}</div>` : ''}
        ${tags ? `<div class="product-tags">${tags}</div>` : ''}
      </div>
      <div class="product-footer">
        <div class="product-price">
          <span class="currency">${esc(p.currency || 'USD')}</span> ${price}
        </div>
        <div class="score-bar-wrap">
          <span class="score-label">Match</span>
          <div class="score-bar">
            <div class="score-fill" style="width:${pct}%"></div>
          </div>
        </div>
      </div>
      ${visitUrl ? `<a href="${esc(visitUrl)}" target="_blank" rel="noopener" class="product-visit-btn">View Product ↗</a>` : ''}
    </article>
  `;
}

function formatPrice(min, max, currency = 'USD') {
  if (min === null && max === null) return '—';
  const fmt = (n) => n.toLocaleString('en-US', { minimumFractionDigits: 2 });
  if (min === max || max === null) return fmt(min ?? 0);
  return `${fmt(min ?? 0)} – ${fmt(max ?? 0)}`;
}

// ── Cached products ───────────────────────────────────────────
loadCachedBtn.addEventListener('click', loadCachedProducts);

async function loadCachedProducts() {
  loadCachedBtn.disabled = true;
  loadCachedBtn.textContent = 'Loading…';
  cachedContainer.innerHTML = '';

  try {
    const res = await fetch(`${API.PRODUCTS}?limit=100`);
    if (!res.ok) throw new Error(res.statusText);
    const products = await res.json();

    if (!products.length) {
      cachedContainer.innerHTML = '<div class="empty-state">No cached products yet. Run a search first.</div>';
      return;
    }

    const grid = document.createElement('div');
    grid.className = 'results-grid';
    grid.innerHTML = products.map((p, i) => buildProductCard(p, i + 1)).join('');
    cachedContainer.appendChild(grid);
    showToast(`Loaded ${products.length} cached products`);
  } catch (err) {
    cachedContainer.innerHTML = `<div class="error-state">⚠️ ${err.message}</div>`;
    showToast(`❌ ${err.message}`, 'danger');
  } finally {
    loadCachedBtn.disabled = false;
    loadCachedBtn.textContent = 'Reload';
  }
}

// ── Utility ───────────────────────────────────────────────────
function esc(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
