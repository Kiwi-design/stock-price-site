YAHOO_CHART_BASES = [
    "https://query1.finance.yahoo.com/v8/finance/chart/",
    "https://query2.finance.yahoo.com/v8/finance/chart/",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

results = []
errors = []

for sym in symbols:
    last_err = None
    chart_json = None

    for base in YAHOO_CHART_BASES:
        url = f"{base}{sym}?interval=1d&range=1d"

        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": UA})
            with urlopen(req, timeout=15) as r:
                chart_json = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            last_err = e
            chart_json = None

    if chart_json is None:
        errors.append({"symbol": sym, "message": f"Yahoo chart failed: {type(last_err).__name__}: {last_err}"})
        continue

    # Parse v8 chart response
    try:
        chart = chart_json.get("chart", {})
        err = chart.get("error")
        if err:
            errors.append({"symbol": sym, "message": f"Yahoo error: {err}"})
            continue

        res0 = (chart.get("result") or [None])[0]
        if not res0:
            errors.append({"symbol": sym, "message": "Yahoo chart: missing result"})
            continue

        meta = res0.get("meta", {})
        price = meta.get("regularMarketPrice")
        currency = meta.get("currency")
        exch = meta.get("exchangeName") or meta.get("fullExchangeName")
        name = meta.get("shortName") or meta.get("longName")

        results.append({
            "symbol": meta.get("symbol", sym),
            "name": name,
            "exchange": exch,
            "currency": currency,
            "datetime": None,
            "price": price,
            "change": None,
            "percent_change": None,
        })

    except Exception as e:
        errors.append({"symbol": sym, "message": f"Parse failed: {type(e).__name__}: {e}"})

self._send(200, {"status": "ok", "symbols": symbols, "results": results, "errors": errors})
