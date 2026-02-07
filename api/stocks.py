from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os
import json

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
        if not symbols_env.strip():
            self._send(500, {"status": "error", "message": "Server misconfigured: missing STOCK_SYMBOLS"})
            return

        symbols = [s.strip().upper() for s in symbols_env.split(",") if s.strip()]
        if not symbols:
            self._send(500, {"status": "error", "message": "STOCK_SYMBOLS is empty"})
            return

        api_key = os.environ.get("TWELVE_DATA_API_KEY", "")
        if not api_key:
            self._send(500, {"status": "error", "message": "Server misconfigured: missing TWELVE_DATA_API_KEY"})
            return

        # --- Fetch quotes one-by-one (simple + reliable) ---
        results = []
        errors = []

        for sym in symbols:
            url = "https://api.twelvedata.com/quote?" + urlencode({"symbol": sym, "apikey": api_key})

            try:
                req = Request(url, headers={"Accept": "application/json", "User-Agent": "vercel-stocks/1.0"})
                with urlopen(req, timeout=15) as r:
                    data = json.loads(r.read().decode("utf-8"))

                # Twelve Data errors often come back as JSON with status=error
                if isinstance(data, dict) and data.get("status") == "error":
                    errors.append({"symbol": sym, "message": data.get("message", "Unknown error")})
                    continue

                price = data.get("close") or data.get("price")
                results.append({
                    "symbol": data.get("symbol", sym),
                    "name": data.get("name"),
                    "exchange": data.get("exchange"),
                    "currency": data.get("currency"),
                    "datetime": data.get("datetime"),
                    "price": price,
                    "change": data.get("change"),
                    "percent_change": data.get("percent_change"),
                })

            except HTTPError as e:
                try:
                    body = e.read().decode("utf-8", errors="replace")
                except Exception:
                    body = ""
                errors.append({"symbol": sym, "message": f"HTTPError {e.code}", "body": body[:300]})

            except URLError as e:
                errors.append({"symbol": sym, "message": f"URLError: {getattr(e, 'reason', str(e))}"})

            except Exception as e:
                errors.append({"symbol": sym, "message": f"Exception: {e.__class__.__name__}: {str(e)}"})

        self._send(200, {"status": "ok", "symbols": symbols, "results": results, "errors": errors})
