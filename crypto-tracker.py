#!/usr/bin/env python3
"""
crypto-tracker.py — Beautiful cryptocurrency price tracker CLI

Pure Python 3.7+, zero dependencies. Fetches live prices from CoinGecko
free API. Great for dashboards, scripts, or just watching markets.

Usage:
    python crypto-tracker.py                          # Default: BTC ETH SOL LTC
    python crypto-tracker.py bitcoin ethereum         # Specific coins
    python crypto-tracker.py --watch                   # Live updates every 30s
    python crypto-tracker.py --json                    # JSON output (pipeable)
    python crypto-tracker.py --csv                     # CSV output
    python crypto-tracker.py --help                    # Full help

Examples:
    # Watch BTC and ETH live
    python crypto-tracker.py --watch bitcoin ethereum

    # Pipe to jq for custom processing
    python crypto-tracker.py --json bitcoin | jq '.bitcoin.usd'

    # CSV for spreadsheet
    python crypto-tracker.py --csv bitcoin ethereum solana > prices.csv

Support: https://github.com/yourusername/crypto-tracker
BTC Tips: 1KPUa9Njq86NJwmwqVmdjZ4oC8eHrXKqf9
"""

import sys
import json
import time
import urllib.request
from datetime import datetime

DEFAULT_COINS = ["bitcoin", "ethereum", "solana", "litecoin"]
COIN_SYMBOLS = {
    "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
    "litecoin": "LTC", "cardano": "ADA", "polkadot": "DOT",
    "chainlink": "LINK", "avalanche-2": "AVAX", "ripple": "XRP",
    "dogecoin": "DOGE", "polygon": "MATIC", "cosmos": "ATOM",
    "uniswap": "UNI", "stellar": "XLM", "monero": "XMR",
}

BTC_TIP = "1KPUa9Njq86NJwmwqVmdjZ4oC8eHrXKqf9"


def fetch_prices(coin_ids):
    """Fetch current prices from CoinGecko free API"""
    ids = ",".join(coin_ids)
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd,eur,btc"
        f"&include_24hr_change=true&include_market_cap=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "crypto-tracker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def format_price(usd):
    """Format price with commas"""
    if isinstance(usd, (int, float)):
        return f"${usd:,.2f}"
    return str(usd)


def display_table(data, coin_ids):
    """Display prices as a formatted table"""
    if "error" in data:
        print(f"❌ Error: {data['error']}")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n  ╔══════════════════════════════════════════════════════════════╗")
    print(f"  ║           📊 CRYPTO PRICE TRACKER                          ║")
    print(f"  ╚══════════════════════════════════════════════════════════════╝")
    print(f"  Updated: {now}")
    print()

    header = f"  {'COIN':<12} {'PRICE (USD)':>14} {'24H CHANGE':>14} {'MARKET CAP':>14}"
    sep = "  " + "─" * 54
    print(header)
    print(sep)

    for coin in coin_ids:
        if coin in data:
            info = data[coin]
            symbol = COIN_SYMBOLS.get(coin, coin[:4].upper())
            usd = info.get("usd", "N/A")
            change = info.get("usd_24h_change", 0)
            mcap = info.get("usd_market_cap", 0)

            change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else "N/A"
            arrow = "▲" if isinstance(change, (int, float)) and change >= 0 else "▼"
            mcap_str = format_price(mcap) if mcap else "N/A"

            print(f"  {symbol:<12} {format_price(usd):>14} {change_str:>14} {arrow}  {mcap_str:>14}")

    print()
    print(f"  💰 BTC Tips: {BTC_TIP}")
    print(f"  📦 Source: https://github.com/yourusername/crypto-tracker\n")


def display_json(data):
    """Output as JSON for piping"""
    print(json.dumps(data, indent=2))


def display_csv(data, coin_ids):
    """Output as CSV"""
    print("coin,symbol,price_usd,change_24h,market_cap")
    for coin in coin_ids:
        if coin in data:
            info = data[coin]
            symbol = COIN_SYMBOLS.get(coin, coin[:4].upper())
            usd = info.get("usd", 0)
            change = info.get("usd_24h_change", 0)
            mcap = info.get("usd_market_cap", 0)
            print(f"{coin},{symbol},{usd},{change},{mcap}")


def watch_mode(coin_ids, interval=30):
    """Live watch mode with change detection"""
    print(f"\n🔍 LIVE WATCH MODE (updates every {interval}s)")
    print("Press Ctrl+C to stop\n")
    last_prices = {}

    try:
        while True:
            data = fetch_prices(coin_ids)
            if "error" in data:
                print(f"  ⚠️  API error: {data['error']}")
                time.sleep(5)
                continue

            # Detect significant price changes
            for coin in coin_ids:
                if coin in data:
                    usd = data[coin].get("usd")
                    if usd and coin in last_prices:
                        pct = ((usd - last_prices[coin]) / last_prices[coin]) * 100
                        if abs(pct) > 0.5:
                            symbol = COIN_SYMBOLS.get(coin, coin[:4].upper())
                            arrow = "▲" if pct > 0 else "▼"
                            print(f"  📢 {symbol} ${usd:,.2f} ({pct:+.2f}%) {arrow}")

                    if usd:
                        last_prices[coin] = usd

            # Show full table
            display_table(data, coin_ids)
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped. Happy trading!\n")


def parse_args(args):
    """Parse command line arguments"""
    flags = []
    coins = []

    for arg in args:
        if arg.startswith("--"):
            flags.append(arg[2:])
        elif arg.startswith("-"):
            flags.append(arg[1:])
        else:
            coins.append(arg.lower())

    return flags, coins


def main():
    args = sys.argv[1:]

    if not args:
        # No args = show default coins
        flags = []
        coins = DEFAULT_COINS
    elif "--help" in args or "-h" in args:
        print(__doc__)
        return
    else:
        flags, coins = parse_args(args)
        if not coins:
            coins = DEFAULT_COINS

    if "json" in flags:
        data = fetch_prices(coins)
        display_json(data)
    elif "csv" in flags:
        data = fetch_prices(coins)
        display_csv(data, coins)
    elif "watch" in flags:
        watch_mode(coins)
    else:
        data = fetch_prices(coins)
        display_table(data, coins)


if __name__ == "__main__":
    main()
