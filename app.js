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
      output.innerHTML = `<div style="color:red; white-space:pre-wrap;">
Error (${res.status}):
${data.message || JSON.stringify(data, null, 2)}
</div>`;
      return;
    }

    let total = 0;

    let html = `
      <table border="1" cellpadding="6" cellspacing="0">
        <thead>
          <tr>
            <th>Name</th>
            <th>Symbol</th>
            <th>Price</th>
            <th>Currency</th>
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
          <td>${price.toFixed(2)}</td>
          <td>${ccy}</td>
          <td>${qty}</td>
          <td>${value.toFixed(2)}</td>
        </tr>
      `;
    }

    html += `
        </tbody>
        <tfoot>
          <tr>
            <td colspan="5"><strong>Total</strong></td>
            <td><strong>${total.toFixed(2)}</strong></td>
          </tr>
        </tfoot>
      </table>
    `;

    output.innerHTML = html;

  } catch (err) {
    output.innerHTML = `<div style="color:red; white-space:pre-wrap;">
Fetch failed:
${String(err)}
</div>`;
  }
});
