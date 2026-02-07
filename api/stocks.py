from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
import json
import os

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

YAHOO_BASES = [
    "https://query1.finance.yahoo.com/v8/finance/chart/",
    "https://query2.finance.yahoo.com/v8/finance/chart/",
]

class handler(BaseHTTPRequestHandler):

    def _send(self, status, obj):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _fetch_yahoo(self, symbol):
        for base in YAHOO_BASES:
            try:
                req = Request(
                    f"{base}{symbol}?interval=1d&range=1d",
                    headers={"User-Agent": UA, "Accept": "application/json"},
                )
                with urlopen(req, timeout=10) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception:
                continue
        return None

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)

        # ---- auth ----
        if qs.get("password", [""])[0] != os.environ.get("APP_PASSWORD", ""):
            self._send(401, {"status": "error", "message": "Unauthorized"})
            return

        # ---- symbols ----
        symbols = [
            s.strip().upper()
            for s in os.environ.get("STOCK_SYMBOLS", "").split(",")
            if s.strip()
        ]
        if not symbols:
            self._send(500, {"status": "error", "message": "STOCK_SYMBOLS empty"})
            return

        # ---- quantities ----
        qty_map = {}
        for pair in os.environ.get("ASSET_QUANTITIES", "").split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                try:
                    qty_map[k.strip().upper()] = float(v)
                except ValueError:
                    pass

        results = []
        errors = []

        # ---- FX cache (per request) ----
        fx_cache = {}

        def fx_to_eur(ccy):
            if ccy == "EUR":
                return 1.0
            if ccy in fx_cache:
                return fx_cache[ccy]

            fx_symbol = f"EUR{ccy}=X"
            data = self._fetch_yahoo(fx_symbol)
            if not data:
                fx_cache[ccy] = None
                return None

            try:
                rate = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
                fx_cache[ccy] = rate
                return rate
            except Exception:
                fx_cache[ccy] = None
                return None

        # ---- assets ----
        for sym in symbols:
            data = self._fetch_yahoo(sym)
            if not data:
                errors.append({"symbol": sym, "message": "Yahoo fetch failed"})
                continue

            try:
                meta = data["chart"]["result"][0]["meta"]

                symbol_out = meta.get("symbol", sym)
                price = meta.get("regularMarketPrice")
                ccy = meta.get("currency")
                qty = qty_map.get(symbol_out, 0)
                value = price * qty if price is not None else None

                rate = fx_to_eur(ccy)
                value_eur = value * rate if value is not None and rate else None

                results.append({
                    "symbol": symbol_out,
                    "name": meta.get("shortName") or meta.get("longName"),
                    "price": price,
                    "currency": ccy,
                    "quantity": qty,
                    "value": value,
                    "value_eur": value_eur,
                    "exchange": meta.get("exchangeName"),
                })

            except Exception as e:
                errors.append({"symbol": sym, "message": str(e)})

        self._send(200, {
            "status": "ok",
            "results": results,
            "errors": errors,
        })
