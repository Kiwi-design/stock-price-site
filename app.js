const API_BASE = "https://stock-price-site-plum.vercel.app"; // change later

const form = document.getElementById("form");
const output = document.getElementById("output");

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const symbol = document.getElementById("symbol").value.trim().toUpperCase();
  output.textContent = "Loading...";

  const url = `${API_BASE}/api/quote?symbol=${symbol}`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = "Error fetching data";
  }
});
