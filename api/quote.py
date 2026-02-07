from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        api_key = os.environ.get("TWELVE_DATA_API_KEY")
        if not api_key:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"error","message":"Missing TWELVE_DATA_API_KEY"}')
            return

        qs = parse_qs(urlparse(self.path).query)
        symbol = (qs.get("symbol", [""])[0] or "").strip().upper()

        if not symbol:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"error","message":"Missing ?symbol="}')
            return

        url = "https://api.twelvedata.com/quote?" + urlencode({"symbol": symbol, "apikey": api_key})

        try:
            req = Request(url, headers={"Accept": "application/json"})
            with urlopen(req, timeout=10) as r:
                body = r.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"error","message":"Upstream request failed"}')
