import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import psycopg2
from pathlib import Path

# ===== Hand picked ETFs =====
picked_etfs = [
    # Broad US market
    "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM", "RSP",
    # Sector
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "XLRE",
    # International / regional
    "VEA", "VWO", "EFA", "EEM", "IEFA", "IEMG", "VGK", "EWJ", "FXI", "MCHI",
    # Bonds / fixed income
    "AGG", "BND", "TLT", "IEF", "SHY", "LQD", "HYG", "TIP",
    # Commodities
    "GLD", "SLV", "USO", "DBC",
    # Thematic / growth
    "ARKK", "SOXX", "SMH", "ICLN", "ROBO", "SKYY",
    # Dividend / value
    "VYM", "SCHD", "VIG", "DVY",
    # Volatility / other
    "VXX", "VNQ",
]

etf_names = {
    # Broad US market
    "SPY": "SPDR S&P 500 ETF Trust",
    "VOO": "Vanguard S&P 500 ETF",
    "IVV": "iShares Core S&P 500 ETF",
    "VTI": "Vanguard Total Stock Market ETF",
    "QQQ": "Invesco QQQ Trust",
    "DIA": "SPDR Dow Jones Industrial Average ETF",
    "IWM": "iShares Russell 2000 ETF",
    "RSP": "Invesco S&P 500 Equal Weight ETF",

    # Sector
    "XLK": "Technology Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLV": "Health Care Select Sector SPDR Fund",
    "XLY": "Consumer Discretionary Select Sector SPDR Fund",
    "XLP": "Consumer Staples Select Sector SPDR Fund",
    "XLI": "Industrial Select Sector SPDR Fund",
    "XLU": "Utilities Select Sector SPDR Fund",
    "XLB": "Materials Select Sector SPDR Fund",
    "XLRE": "Real Estate Select Sector SPDR Fund",

    # International / regional
    "VEA": "Vanguard FTSE Developed Markets ETF",
    "VWO": "Vanguard FTSE Emerging Markets ETF",
    "EFA": "iShares MSCI EAFE ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "IEFA": "iShares Core MSCI EAFE ETF",
    "IEMG": "iShares Core MSCI Emerging Markets ETF",
    "VGK": "Vanguard FTSE Europe ETF",
    "EWJ": "iShares MSCI Japan ETF",
    "FXI": "iShares China Large-Cap ETF",
    "MCHI": "iShares MSCI China ETF",

    # Bonds / fixed income
    "AGG": "iShares Core U.S. Aggregate Bond ETF",
    "BND": "Vanguard Total Bond Market ETF",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "IEF": "iShares 7-10 Year Treasury Bond ETF",
    "SHY": "iShares 1-3 Year Treasury Bond ETF",
    "LQD": "iShares iBoxx Investment Grade Corporate Bond ETF",
    "HYG": "iShares iBoxx High Yield Corporate Bond ETF",
    "TIP": "iShares TIPS Bond ETF",

    # Commodities
    "GLD": "SPDR Gold Shares",
    "SLV": "iShares Silver Trust",
    "USO": "United States Oil Fund",
    "DBC": "Invesco DB Commodity Index Tracking Fund",

    # Thematic / growth
    "ARKK": "ARK Innovation ETF",
    "SOXX": "iShares Semiconductor ETF",
    "SMH": "VanEck Semiconductor ETF",
    "ICLN": "iShares Global Clean Energy ETF",
    "ROBO": "ROBO Global Robotics and Automation ETF",
    "SKYY": "First Trust Cloud Computing ETF",

    # Dividend / value
    "VYM": "Vanguard High Dividend Yield ETF",
    "SCHD": "Schwab US Dividend Equity ETF",
    "VIG": "Vanguard Dividend Appreciation ETF",
    "DVY": "iShares Select Dividend ETF",

    # Volatility / other
    "VXX": "iPath Series B S&P 500 VIX Short-Term Futures ETN",
    "VNQ": "Vanguard Real Estate ETF",
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

df_prices = download_prices(picked_etfs)

latest_prices = df_prices.sort_values("Date").groupby("Ticker").tail(1)

# Adding ETF name.
latest_prices["Name"] = latest_prices["Ticker"].map(etf_names)

# Prices are in USD, so we change them to EUR.
eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
eurusd = float(eurusd.iloc[-1])
latest_prices["Price"] = latest_prices["Close"] / eurusd

# Adding asset type.
latest_prices["Asset_Type"] = "ETF"

# Adding time when prices were taken.
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
latest_prices["Time"] = current_time

latest_prices = latest_prices[["Name", "Ticker", "Asset_Type", "Price", "Date", "Time"]]
latest_prices = pd.DataFrame(latest_prices)



SCRIPT_DIR = Path(__file__).resolve().parent
latest_prices.to_csv(SCRIPT_DIR / "etfs.csv", index=False)


#Filling the database with data
conn = psycopg2.connect(host="baza.fmf.uni-lj.si", dbname="sem2026_nejczi", user="javnost", password="javnogeslo")
cur = conn.cursor()
with open('etfs.csv', 'r') as f:
    next(f) # Skip the header row.
    cur.copy_from(f, 'asset', sep=',', columns=('asset_name', 'asset_symbol', 'asset_type', 'price', 'date_stamp', 'time_stamp'))

conn.commit()