const API_BASE = "https://stock-price-site-nine.vercel.app"; // <- your Vercel URL

const form = document.getElementById("form");
const output = document.getElementById("output");
const passwordEl = document.getElementById("password");

if (!form) {
  throw new Error("Missing <form id='form'> in index.html");
}
if (!output) {
  throw new Error("Missing <pre id='output'> in index.html");
}
if (!passwordEl) {
  output.textContent = "ERROR: Missing <input id='password'> in index.html";
} else {
  output.textContent = "Ready. Enter password and press the button.";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const password = passwordEl ? passwordEl.value : "";
  output.textContent = "Submitting...";

  const url = new URL(`${API_BASE}/api/stocks`);
  url.searchParams.set("password", password);

  try {

  const res = await fetch(url.toString());
  const data = await res.json();

if (!res.ok || data.status !== "ok") {
  output.textContent = `Error (${res.status}): ${data.message || JSON.stringify(data)}`;
  return;
}

// Show only prices (one per line)
output.textContent = data.results
  .map(r => `${r.name} (${r.symbol}): ${r.price} ${r.currency}`)
  .join("\n");

    
  } catch (err) {
    output.textContent = `Fetch failed:\n${String(err)}`;
  }
});
