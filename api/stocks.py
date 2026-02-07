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

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)

        # password check
        if qs.get("password", [""])[0] != os.environ.get("APP_PASSWORD", ""):
            self._send(401, {"status": "error", "message": "Unauthorized"})
            return

        symbols = os.environ.get("STOCK_SYMBOLS", "")
        symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        if not symbols:
            self._send(500, {"status": "error", "message": "STOCK_SYMBOLS empty"})
            return

        results = []
        errors = []

        for sym in symbols:
            data = None
            last_err = None

            for base in YAHOO_BASES:
                try:
                    req = Request(
                        f"{base}{sym}?interval=1d&range=1d",
                        headers={"User-Agent": UA, "Accept": "application/json"},
                    )
                    with urlopen(req, timeout=10) as r:
                        data = json.loads(r.read().decode("utf-8"))
                    break
                except Exception as e:
                    last_err = e
                    data = None

            if not data:
                errors.append({"symbol": sym, "message": str(last_err)})
                continue

            chart = data.get("chart", {})
            if chart.get("error"):
                errors.append({"symbol": sym, "message": chart["error"]})
                continue

            res = chart["result"][0]
            meta = res["meta"]

            results.append({
                "symbol": meta.get("symbol", sym),
                "price": meta.get("regularMarketPrice"),
                "currency": meta.get("currency"),
                "exchange": meta.get("exchangeName"),
            })

        self._send(200, {
            "status": "ok",
            "results": results,
            "errors": errors,
        })
