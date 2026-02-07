const API_BASE = "https://stock-price-site-nine.vercel.app"; // e.g. https://my-project.vercel.app

const form = document.getElementById("form");
const output = document.getElementById("output");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const symbol = document.getElementById("symbol").value.trim().toUpperCase();
  output.textContent = "Loading...";

  const url = new URL(`${API_BASE}/api/quote`);
  url.searchParams.set("symbol", symbol);

  try {
    const res = await fetch(url.toString());
    const text = await res.text();

    if (!res.ok) {
      output.textContent = `HTTP ${res.status}\n\n${text}\n\nURL:\n${url}`;
      return;
    }

    try {
      const data = JSON.parse(text);
      const price = data.close ?? data.price;
      output.textContent = `${data.symbol}: ${price} ${data.currency}`;
    } catch {
      output.textContent = `Non-JSON response:\n\n${text}\n\nURL:\n${url}`;
    }
  } catch (err) {
    output.textContent = `Fetch failed:\n${String(err)}\n\nURL:\n${url}`;
  }
});
