from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import os

class handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        api_key = os.environ.get("TWELVE_DATA_API_KEY")
        if not api_key:
            self._send(500, b'{"status":"error","message":"Missing TWELVE_DATA_API_KEY"}')
            return

        qs = parse_qs(urlparse(self.path).query)
        symbol = (qs.get("symbol", [""])[0] or "").strip().upper()
        if not symbol:
            self._send(400, b'{"status":"error","message":"Missing ?symbol="}')
            return

        url = "https://api.twelvedata.com/quote?" + urlencode({"symbol": symbol, "apikey": api_key})

        try:
            req = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "vercel-python-proxy/1.0"
                },
            )
            with urlopen(req, timeout=15) as r:
                body = r.read()
                # Pass through whatever Twelve Data returns
                self._send(r.status, body)

        except HTTPError as e:
            # Twelve Data responded with an HTTP error (often 401/429/etc.)
            try:
                body = e.read()
            except Exception:
                body = f'{{"status":"error","message":"HTTPError {e.code}"}}'.encode("utf-8")
            self._send(e.code, body)

        except URLError as e:
            # Network/DNS/TLS/connection issues
            msg = str(getattr(e, "reason", e))
            self._send(502, f'{{"status":"error","message":"URLError: {msg}"}}'.encode("utf-8"))

        except Exception as e:
            # Anything else
            self._send(502, f'{{"status":"error","message":"Exception: {e.__class__.__name__}: {str(e)}"}}'.encode("utf-8"))
