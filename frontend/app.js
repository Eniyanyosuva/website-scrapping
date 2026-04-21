const form = document.getElementById("searchForm");
const resultsEl = document.getElementById("results");
const metaEl = document.getElementById("meta");
const API_BASE = window.location.origin;

function renderResults(data) {
  metaEl.textContent = `Crawled: ${data.total_crawled} | Matched: ${data.total_matched}`;
  resultsEl.innerHTML = "";

  if (!data.results.length) {
    resultsEl.innerHTML = "<p>No matching products found.</p>";
    return;
  }

  for (const product of data.results) {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <a href="${product.product_url}" target="_blank" rel="noreferrer">${product.title}</a>
      <div>Vendor: ${product.vendor}</div>
      <div>Price: ${product.currency} ${Number(product.price).toFixed(2)}</div>
      <div>Score: ${Number(product.score).toFixed(2)}</div>
      <div class="tags">Tags: ${(product.tags || []).join(", ") || "N/A"}</div>
    `;
    resultsEl.appendChild(card);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultsEl.innerHTML = "<p>Searching...</p>";
  metaEl.textContent = "";

  const payload = {
    product_name: document.getElementById("product_name").value.trim(),
    occasion: document.getElementById("occasion").value.trim() || "general",
    budget_min: Number(document.getElementById("budget_min").value),
    budget_max: Number(document.getElementById("budget_max").value),
    preferences: document
      .getElementById("preferences")
      .value.split(",")
      .map((s) => s.trim())
      .filter(Boolean),
    shopify_store_url: document.getElementById("shopify_store_url").value.trim(),
  };

  try {
    const response = await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let err = { detail: "Search request failed" };
      try {
        err = await response.json();
      } catch {
        // Keep fallback message when response body is not JSON.
      }
      throw new Error(err.detail || "Search request failed");
    }

    const data = await response.json();
    renderResults(data);
  } catch (error) {
    const msg = String(error?.message || error);
    if (msg.toLowerCase().includes("failed to fetch")) {
      resultsEl.innerHTML =
        "<p>Cannot reach backend. Start server in terminal: " +
        "<code>python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000</code></p>";
      return;
    }
    resultsEl.innerHTML = `<p>${msg}</p>`;
  }
});
