import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import psycopg2
from pathlib import Path

# ===== Hand picked stocks =====
picked_stocks = [
    # US Tech 
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO", "ORCL", "ADBE",
    "CRM", "AMD", "NFLX", "INTC", "CSCO", "IBM", "QCOM", "TXN", "NOW", "INTU",
    # US finance
    "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "SCHW",
    # US healthcare
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
    # US industry
    "WMT", "PG", "KO", "PEP", "COST", "HD", "MCD", "NKE", "DIS", "CMCSA",
    "XOM", "CVX", "CAT", "BA", "HON", "UPS", "GE", "LMT", "RTX", "DE",
    # US others
    "PM", "T", "VZ", "LIN", "UNP", "LOW", "SBUX", "BLK", "SPGI", "AMT",
    # China
    "BABA", "TCEHY", "PDD", "JD", "BIDU", "NTES",
    # Europe
    "ASML", "NVO", "SAP", "SHEL", "AZN", "UL", "NESN.SW", "MC.PA", "OR.PA",
    "SIE.DE", "ALV.DE", "SAN.PA", "TTE", "BP", "HSBC", "RIO", "BHP", "DTE.DE", "IBE.MC",
    # Japan
    "TM", "SONY", "MUFG", "SMFG", "NTDOY", "HMC",
    # Canada, Australia
    "SHOP", "RY", "TD", "BNS", "CBA.AX",
    # Taiwan, Korea, India
    "TSM", "INFY"
]


stock_names = {
    # US Tech
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "Nvidia",
    "GOOGL": "Alphabet Class A",
    "AMZN": "Amazon",
    "META": "Meta Platforms",
    "TSLA": "Tesla",
    "AVGO": "Broadcom",
    "ORCL": "Oracle",
    "ADBE": "Adobe",
    "CRM": "Salesforce",
    "AMD": "Advanced Micro Devices",
    "NFLX": "Netflix",
    "INTC": "Intel",
    "CSCO": "Cisco Systems",
    "IBM": "IBM",
    "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    "NOW": "ServiceNow",
    "INTU": "Intuit",

    # US Finance
    "BRK-B": "Berkshire Hathaway",
    "JPM": "JPMorgan Chase",
    "V": "Visa",
    "MA": "Mastercard",
    "BAC": "Bank of America",
    "WFC": "Wells Fargo",
    "GS": "Goldman Sachs",
    "MS": "Morgan Stanley",
    "AXP": "American Express",
    "SCHW": "Charles Schwab",

    # US Healthcare
    "LLY": "Eli Lilly",
    "UNH": "UnitedHealth Group",
    "JNJ": "Johnson & Johnson",
    "ABBV": "AbbVie",
    "MRK": "Merck",
    "PFE": "Pfizer",
    "TMO": "Thermo Fisher Scientific",
    "ABT": "Abbott Laboratories",
    "DHR": "Danaher",
    "BMY": "Bristol-Myers Squibb",

    # US Industry 
    "WMT": "Walmart",
    "PG": "Procter & Gamble",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "COST": "Costco",
    "HD": "Home Depot",
    "MCD": "McDonald's",
    "NKE": "Nike",
    "DIS": "Disney",
    "CMCSA": "Comcast",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "CAT": "Caterpillar",
    "BA": "Boeing",
    "HON": "Honeywell",
    "UPS": "UPS",
    "GE": "General Electric",
    "LMT": "Lockheed Martin",
    "RTX": "RTX Corporation",
    "DE": "Deere & Company",

    # US Others
    "PM": "Philip Morris International",
    "T": "AT&T",
    "VZ": "Verizon",
    "LIN": "Linde",
    "UNP": "Union Pacific",
    "LOW": "Lowe's",
    "SBUX": "Starbucks",
    "BLK": "BlackRock",
    "SPGI": "S&P Global",
    "AMT": "American Tower",

    # China
    "BABA": "Alibaba",
    "TCEHY": "Tencent",
    "PDD": "Pinduoduo",
    "JD": "JD.com",
    "BIDU": "Baidu",
    "NTES": "NetEase",

    # Europe
    "ASML": "ASML Holding",
    "NVO": "Novo Nordisk",
    "SAP": "SAP",
    "SHEL": "Shell",
    "AZN": "AstraZeneca",
    "UL": "Unilever",
    "NESN.SW": "Nestlé",
    "MC.PA": "LVMH",
    "OR.PA": "L'Oréal",
    "SIE.DE": "Siemens",
    "ALV.DE": "Allianz",
    "SAN.PA": "Sanofi",
    "TTE": "TotalEnergies",
    "BP": "BP",
    "HSBC": "HSBC",
    "RIO": "Rio Tinto",
    "BHP": "BHP Group",
    "DTE.DE": "Deutsche Telekom",
    "IBE.MC": "Iberdrola",

    # Japan
    "TM": "Toyota",
    "SONY": "Sony Group",
    "MUFG": "Mitsubishi UFJ Financial Group",
    "SMFG": "Sumitomo Mitsui Financial Group",
    "NTDOY": "Nintendo",
    "HMC": "Honda",

    # Canada, Australia
    "SHOP": "Shopify",
    "RY": "Royal Bank of Canada",
    "TD": "Toronto-Dominion Bank",
    "BNS": "Bank of Nova Scotia",
    "CBA.AX": "Commonwealth Bank of Australia",

    # Taiwan, Korea, India
    "TSM": "Taiwan Semiconductor Manufacturing",
    "INFY": "Infosys"
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

# Close price is equal to the actual price.
df_prices = download_prices(picked_stocks)
latest_prices = df_prices.sort_values("Date").groupby("Ticker").tail(1)

# Adding Stock name.
latest_prices["Name"] = latest_prices["Ticker"].map(stock_names)

# Prices are in USD, so we change them to EUR.
eurusd = yf.download("EURUSD=X", period="1d")["Close"].iloc[-1]
eurusd = float(eurusd.iloc[-1])
latest_prices["Price"] = latest_prices["Close"] / eurusd

# Adding asset type.
latest_prices["Asset_Type"] = "Stock"

# Adding time when prices were taken.
now = datetime.now()
current_time =now.strftime("%H:%M:%S")
latest_prices["Time"] = current_time

# Selecting the wanted columns.
latest_prices = latest_prices[["Name", "Ticker", "Asset_Type", "Price", "Date",  "Time"]]
latest_prices = pd.DataFrame(latest_prices)

# Adding path to the wanted folder and creating csv.
SCRIPT_DIR = Path(__file__).resolve().parent
latest_prices.to_csv(SCRIPT_DIR / 'stocks.csv', index=False)


# Filling the database with data.
conn = psycopg2.connect(host="baza.fmf.uni-lj.si", dbname="sem2026_nejczi", user="javnost", password="javnogeslo")
cur = conn.cursor()
with open('stocks.csv', 'r') as f:
    next(f) # Skip the header row.
    cur.copy_from(f, 'asset', sep=',', columns=('asset_name', 'asset_symbol', 'asset_type', 'price', 'date_stamp', 'time_stamp'))

conn.commit()