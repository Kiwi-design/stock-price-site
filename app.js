const API_BASE = "https://stock-price-site-nine.vercel.app";

const form = document.getElementById("form");
const output = document.getElementById("output");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = document.getElementById("password").value;
  output.textContent = "Loading...";

  const url = new URL(`${API_BASE}/api/stocks`);
  url.searchParams.set("password", password);

  try {
    const res = await fetch(url.toString());
    const data = await res.json();

    if (!res.ok || data.status !== "ok") {
      output.textContent = `Error (${res.status}): ${data.message || JSON.stringify(data)}`;
      return;
    }

    // Show a simple readable list
    const lines = data.results.map(r =>
      `${r.symbol}: ${r.price} ${r.currency} (Δ ${r.change}, ${r.percent_change}%)`
    );

    if (data.errors?.length) {
      lines.push("\nErrors:");
      data.errors.forEach(err => lines.push(`${err.symbol}: ${err.message}`));
    }

    output.textContent = lines.join("\n");
  } catch (err) {
    output.textContent = `Fetch failed: ${String(err)}`;
  }
});
