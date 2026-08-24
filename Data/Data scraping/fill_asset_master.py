import yfinance as yf
import pandas as pd
from pathlib import Path
import asset_data
import download_assets
import psycopg2

# Getting data about selected assets.
stock_prices = download_assets.download_assets(asset_data.picked_stocks)
etf_prices = download_assets.download_assets(asset_data.picked_etfs)
crypto_prices = download_assets.download_assets(asset_data.picked_cryptos)

# Picking only the latest information about the stock.
stock_prices = stock_prices.sort_values("Date").groupby("Ticker").tail(1)
etf_prices = etf_prices.sort_values("Date").groupby("Ticker").tail(1)
crypto_prices = crypto_prices.sort_values("Date").groupby("Ticker").tail(1)

# Adding stock name.
stock_prices["Name"] = stock_prices["Ticker"].map(asset_data.stock_names)
etf_prices["Name"] = etf_prices["Ticker"].map(asset_data.etf_names)
crypto_prices["Name"] = crypto_prices["Ticker"].map(asset_data.crypto_names)

# Adding asset type.
stock_prices["Asset_Type"] = "Stock"
etf_prices["Asset_Type"] = "ETF"
crypto_prices["Asset_Type"] = "Crypto"

# Joining all three df.
asset_master = pd.concat([stock_prices, etf_prices, crypto_prices], ignore_index=True)

# Selecting the wanted columns.
asset_master = asset_master[["Name", "Ticker", "Asset_Type"]]
asset_master = pd.DataFrame(asset_master)

# Adding path to the wanted folder and creating csv.
SCRIPT_DIR = Path(__file__).resolve().parent
asset_master.to_csv(SCRIPT_DIR / 'asset_master.csv', index=False)

# Filling the database with data.
conn = psycopg2.connect(host="baza.fmf.uni-lj.si", dbname="sem2026_nejczi", user="javnost", password="javnogeslo")
cur = conn.cursor()
with open(SCRIPT_DIR / 'asset_master.csv', 'r') as f:
    next(f) # Skip the header row.
    cur.copy_from(f, 'asset_master', sep=',', columns=('asset_name', 'asset_symbol', 'asset_type'))

conn.commit()
