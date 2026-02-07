from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import json

YAHOO_QUOTE_V7 = "https://query1.finance.yahoo.com/v7/finance/quote"
YAHOO_QUOTE_V6 = "https://query1.finance.yahoo.com/v6/finance/quote"  # fallback if v7 ever breaks :contentReference[oaicite:2]{index=2}

def _json_bytes(obj) -> bytes:
    return json.dumps(obj).encode("utf-8")

class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, obj: dict):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(_json_bytes(obj))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        # --- Password check ---
        app_pw = os.environ.get("APP_PASSWORD", "")
        qs = parse_qs(urlparse(self.path).query)
        provided = (qs.get("password", [""])[0] or "").strip()

        if not app_pw:
            self._send(500, {"status": "error", "message": "Server misconfigured: missing APP_PASSWORD"})
            return
        if provided != app_pw:
            self._send(401, {"status": "error", "message": "Unauthorized"})
            return

        # --- Symbols list from env ---
        symbols_env = os.environ.get("STOCK_SYMBOLS", "")
        symbols = [s.strip().upper() for s in symbols_env.split(",") if s.strip()]
        if not symbols:
            self._send(500, {"status": "error", "message": "Server misconfigured: missing/empty STOCK_SYMBOLS"})
            return

        # Yahoo supports multiple symbols in one request :contentReference[oaicite:3]{index=3}
        params = urlencode({"symbols": ",".join(symbols)})
        urls_to_try = [
            f"{YAHOO_QUOTE_V7}?{params}",
            f"{YAHOO_QUOTE_V6}?{params}",  # fallback
        ]

        last_err = None
        data = None

        for url in urls_to_try:
            try:
                req = Request(
                    url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (compatible; vercel-proxy/1.0)",
                    },
                )
                with urlopen(req, timeout=15) as r:
                    data = json.loads(r.read().decode("utf-8"))
                break
            except (HTTPError, URLError, json.JSONDecodeError) as e:
                last_err = e
                data = None

        if data is None:
            self._send(502, {"status": "error", "message": f"Yahoo upstream failed: {str(last_err)}"})
            return

        # Parse Yahoo response structure
        qr = (data.get("quoteResponse") or {})
        results_raw = qr.get("result") or []
        errors = qr.get("error")

        if errors:
            self._send(502, {"status": "error", "message": f"Yahoo error: {errors}"})
            return

        # Map Yahoo fields -> your app fields
        results = []
        for item in results_raw:
            # price: prefer regularMarketPrice
            price = item.get("regularMarketPrice")
            currency = item.get("currency")
            symbol = item.get("symbol")

            # change fields
            change = item.get("regularMarketChange")
            pct = item.get("regularMarketChangePercent")

            # nice labels
            name = item.get("shortName") or item.get("longName")
            exchange = item.get("fullExchangeName") or item.get("exchange")

            results.append({
                "symbol": symbol,
                "name": name,
                "exchange": exchange,
                "currency": currency,
                "datetime": None,              # Yahoo response doesn’t always include a clean datetime
                "price": price,
                "change": change,
                "percent_change": pct,
            })

        # If some symbols didn’t come back, report them
        returned = {r["symbol"] for r in results if r.get("symbol")}
        missing = [s for s in symbols if s not in returned]

        self._send(200, {
            "status": "ok",
            "symbols": symbols,
            "results": results,
            "errors": [{"symbol": s, "message": "Not returned by Yahoo"} for s in missing],
        })
