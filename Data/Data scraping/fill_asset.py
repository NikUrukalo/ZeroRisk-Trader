import yfinance as yf
import pandas as pd
from datetime import datetime
import psycopg2
from pathlib import Path
import asset_data
import download_assets

# Getting prices for picked assets
stock_prices = download_assets.download_assets(asset_data.picked_stocks)
etf_prices = download_assets.download_assets(asset_data.picked_etfs)
crypto_prices = download_assets.download_assets(asset_data.picked_cryptos)

# Picking only the latest information about the stock.
stock_prices = stock_prices.sort_values("Date").groupby("Ticker").tail(1)
etf_prices = etf_prices.sort_values("Date").groupby("Ticker").tail(1)
crypto_prices = crypto_prices.sort_values("Date").groupby("Ticker").tail(1)

# Prices are in USD, so we change them to EUR.
eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
eurusd = float(eurusd.iloc[-1])

# Close price is equal to current price of the asset.
stock_prices["Price"] = stock_prices["Close"] / eurusd  
etf_prices["Price"] = etf_prices["Close"] / eurusd
crypto_prices["Price"] = crypto_prices["Close"] / eurusd

# Joining all three df.
asset_prices = pd.concat([stock_prices, etf_prices, crypto_prices], ignore_index=True)

# Adding time and date when prices were taken.
now = datetime.now()
current_time =now.strftime("%H:%M:%S")
asset_prices["Time"] = current_time
current_date = now.date()
asset_prices["Date"] = current_date

# Selecting the wanted columns.
asset_prices = asset_prices[["Ticker", "Price", "Date",  "Time"]]
asset_prices = pd.DataFrame(asset_prices)

# Adding path to the wanted folder and creating csv.
SCRIPT_DIR = Path(__file__).resolve().parent
asset_prices.to_csv(SCRIPT_DIR / 'asset_prices.csv', index=False)

# Filling the database with data.
conn = psycopg2.connect(host="baza.fmf.uni-lj.si", dbname="sem2026_nejczi", user="javnost", password="javnogeslo")
cur = conn.cursor()
with open(SCRIPT_DIR / 'asset_prices.csv', 'r') as f:
    next(f) # Skip the header row.
    cur.copy_from(f, 'asset', sep=',', columns=('asset_symbol', 'price', 'date_stamp', 'time_stamp'))

conn.commit()

