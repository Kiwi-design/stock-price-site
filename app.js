const API_BASE = "https://stock-price-site-nine.vercel.app"; // <- your Vercel URL

const form = document.getElementById("form");
const output = document.getElementById("output");
const passwordEl = document.getElementById("password");

output.textContent = "Enter password and click “Load portfolio”.";

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = passwordEl.value;
  output.textContent = "Loading…";

  const url = new URL(`${API_BASE}/api/stocks`);
  url.searchParams.set("password", password);

  try {
    const res = await fetch(url.toString());
    const data = await res.json();

    if (!res.ok || data.status !== "ok") {
      output.innerHTML = `<div class="error">
Error (${res.status}):
${data.message || JSON.stringify(data, null, 2)}
</div>`;
      return;
    }

    let total = 0;

    let html = `
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Symbol</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
    `;

    for (const r of data.results) {
      const price = r.price ?? 0;
      const qty = r.quantity ?? 0;
      const value = r.value ?? 0;
      const ccy = r.currency ?? "";

      total += value;

      html += `
        <tr>
          <td>${r.name || ""}</td>
          <td>${r.symbol}</td>
          <td>${price.toFixed(2)} ${ccy}</td>
          <td>${qty}</td>
          <td>${value.toFixed(2)} ${ccy}</td>
        </tr>
      `;
    }

    html += `
        </tbody>
        <tfoot>
          <tr>
            <td colspan="4">Total</td>
            <td>${total.toFixed(2)}</td>
          </tr>
        </tfoot>
      </table>
    `;

    output.innerHTML = html;

  } catch (err) {
    output.innerHTML = `<div class="error">
Fetch failed:
${String(err)}
</div>`;
  }
});
