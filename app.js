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
      <table style="
        border-collapse: collapse;
        min-width: 700px;
        font-family: Arial, sans-serif;
      ">
        <thead>
          <tr>
            <th style="text-align:left; padding:10px 14px; border-bottom:2px solid #ccc;">Name</th>
            <th style="text-align:left; padding:10px 14px; border-bottom:2px solid #ccc;">Symbol</th>
            <th style="text-align:right; padding:10px 14px; border-bottom:2px solid #ccc;">Price</th>
            <th style="text-align:left; padding:10px 14px; border-bottom:2px solid #ccc;">Currency</th>
            <th style="text-align:right; padding:10px 14px; border-bottom:2px solid #ccc;">Quantity</th>
            <th style="text-align:right; padding:10px 14px; border-bottom:2px solid #ccc;">Value in ccy</th>
            <th style="text-align:right; padding:10px 14px; border-bottom:2px solid #ccc;">Value in EUR</th>
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
          <td style="text-align:left; padding:8px 14px;">${r.name || ""}</td>
          <td style="text-align:left; padding:8px 14px;">${r.symbol}</td>
          <td style="text-align:right; padding:8px 14px;">${price.toFixed(2)}</td>
          <td style="text-align:left; padding:8px 14px;">${ccy}</td>
          <td style="text-align:right; padding:8px 14px;">${qty}</td>
          <td style="text-align:right; padding:8px 14px;">${value.toFixed(2)}</td>
          <td style="text-align:right; padding:8px 14px;">${r.value_eur !== null ? r.value_eur.toFixed(2) : ""}</td>
        </tr>
      `;
    }

    html += `
        </tbody>
        <tfoot>
          <tr>
            <td colspan="5" style="
              text-align:right;
              padding:10px 14px;
              border-top:2px solid #ccc;
              font-weight:bold;
            ">
              Total
            </td>
            <td style="
              text-align:right;
              padding:10px 14px;
              border-top:2px solid #ccc;
              font-weight:bold;
            ">
              ${total.toFixed(2)}
            </td>
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
