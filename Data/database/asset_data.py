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