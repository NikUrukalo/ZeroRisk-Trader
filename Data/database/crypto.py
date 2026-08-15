import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import psycopg2
from pathlib import Path

# ===== Hand picked cryptocurrencies =====
picked_cryptos = [
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "SOL-USD",
    "XRP-USD", "USDC-USD", "ADA-USD", "DOGE-USD", "AVAX-USD",
    "TRX-USD", "DOT-USD", "LINK-USD", "TON-USD", 
    "SHIB-USD", "LTC-USD", "BCH-USD", "NEAR-USD", 
    "ICP-USD", "XLM-USD", "ETC-USD",
    "FIL-USD", "ATOM-USD", "HBAR-USD", "ARB-USD",
    "OP-USD", "VET-USD", "MKR-USD", "AAVE-USD",
    "ALGO-USD", "QNT-USD", "SAND-USD", "MANA-USD", "AXS-USD",
    "EOS-USD", "XTZ-USD", "THETA-USD", "EGLD-USD",
    "RUNE-USD", "CHZ-USD", "KAVA-USD", "ZEC-USD", "SNX-USD",
]

crypto_names = {
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "USDT-USD": "Tether",
    "BNB-USD": "BNB",
    "SOL-USD": "Solana",
    "XRP-USD": "XRP",
    "USDC-USD": "USD Coin",
    "ADA-USD": "Cardano",
    "DOGE-USD": "Dogecoin",
    "AVAX-USD": "Avalanche",
    "TRX-USD": "TRON",
    "DOT-USD": "Polkadot",
    "LINK-USD": "Chainlink",
    "TON-USD": "Toncoin",
    "SHIB-USD": "Shiba Inu",
    "LTC-USD": "Litecoin",
    "BCH-USD": "Bitcoin Cash",
    "NEAR-USD": "NEAR Protocol",
    "ICP-USD": "Internet Computer",
    "XLM-USD": "Stellar",
    "ETC-USD": "Ethereum Classic",
    "FIL-USD": "Filecoin",
    "ATOM-USD": "Cosmos",
    "HBAR-USD": "Hedera",
    "ARB-USD": "Arbitrum",
    "OP-USD": "Optimism",
    "VET-USD": "VeChain",
    "MKR-USD": "Maker",
    "AAVE-USD": "Aave",
    "ALGO-USD": "Algorand",
    "QNT-USD": "Quant",
    "SAND-USD": "The Sandbox",
    "MANA-USD": "Decentraland",
    "AXS-USD": "Axie Infinity",
    "EOS-USD": "EOS",
    "XTZ-USD": "Tezos",
    "THETA-USD": "Theta Network",
    "EGLD-USD": "MultiversX",
    "RUNE-USD": "THORChain",
    "CHZ-USD": "Chiliz",
    "KAVA-USD": "Kava",
    "ZEC-USD": "Zcash",
    "SNX-USD": "Synthetix",
}


def download_prices(tickers, batch_size=25, period="1mo", interval="1d", pause=2):
    all_frames = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        print(f"Downloading batch {i//batch_size + 1}: {batch}")
        data = yf.download(batch, period=period, interval=interval,
                            group_by="ticker", threads=True, auto_adjust=True, actions=False)

        for t in batch:
            try:
                sub = data.xs(t, axis=1, level=0).copy() if len(batch) > 1 else data.copy()
                sub["Ticker"] = t
                sub.reset_index(inplace=True)
                all_frames.append(sub)
            except (KeyError, ValueError):
                print(f"  Ni podatkov za {t}")
        time.sleep(pause)
    return pd.concat(all_frames, ignore_index=True)

df_prices = download_prices(picked_cryptos)

latest_prices = df_prices.sort_values("Date").groupby("Ticker").tail(1)

# Adding crypto name.
latest_prices["Name"] = latest_prices["Ticker"].map(crypto_names)

# Prices are in USD, so we change them to EUR.
eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
eurusd = float(eurusd.iloc[-1])
latest_prices["Price"] = latest_prices["Close"] / eurusd

# Adding asset type.
latest_prices["Asset_Type"] = "Crypto"

# Adding time when prices were taken.
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
latest_prices["Time"] = current_time

latest_prices = latest_prices[["Name", "Ticker", "Asset_Type", "Price", "Date", "Time"]]
latest_prices = pd.DataFrame(latest_prices)

SCRIPT_DIR = Path(__file__).resolve().parent
latest_prices.to_csv(SCRIPT_DIR / 'crypto.csv', index=False)


#Filling the database with data
conn = psycopg2.connect(host="baza.fmf.uni-lj.si", dbname="sem2026_nejczi", user="javnost", password="javnogeslo")
cur = conn.cursor()
with open('crypto.csv', 'r') as f:
    next(f) # Skip the header row.
    cur.copy_from(f, 'asset', sep=',', columns=('asset_name', 'asset_symbol', 'asset_type', 'price', 'date_stamp', 'time_stamp'))

conn.commit()