import os
import json
import urllib.parse
import urllib.request

def handler(request):
    # Read API key from Vercel (secret)
    api_key = os.environ.get("TWELVE_DATA_API_KEY")

    if not api_key:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "API key not configured"})
        }

    # Get stock symbol from the URL
    symbol = request.query.get("symbol", "").upper()

    if not symbol:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing symbol"})
        }

    # Build Twelve Data request
    params = urllib.parse.urlencode({
        "symbol": symbol,
        "apikey": api_key
    })

    url = f"https://api.twelvedata.com/quote?{params}"

    # Call Twelve Data
    with urllib.request.urlopen(url) as response:
        data = response.read().decode("utf-8")

    # Send result back to browser
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": data
    }
