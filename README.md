# ZeroRisk Trader

**Practice trading with zero risk.** ZeroRisk Trader is a web app for simulating stock, ETF, and crypto trading with virtual money — real market prices, a real relational database, and nothing at stake.

> Project for *Osnove podatkovnih baz* (FMF, 2026)
> **Authors:** Nejc Žibret & Nik Urukalo

---

## What it does

You register, get a virtual portfolio, and start trading. Prices for around 200 assets are scraped from Yahoo Finance into a PostgreSQL database on the faculty server, and every order is priced against the latest stored snapshot.

| Page | What it does |
|---|---|
| **Login / Register** | Passwords are stored as bcrypt hashes; sessions run on a cookie. Opening the login page also triggers a price refresh in the background. |
| **Overview** | Cash balance, value of holdings, total portfolio value, every open position with its profit/loss, and the ten most recent trades. |
| **Trade** | Every asset with its latest price, live search by name or symbol, buying/selling in any (including fractional) quantity, and the five biggest movers. |
| **Earn balance** | A finance quiz — a correct answer credits a reward to your balance, followed by a one-hour cooldown. |

---

## ER Diagram

<img width="2146" height="870" alt="ZeroRisk_Trader ER diagram" src="https://github.com/user-attachments/assets/87799eb9-41e5-424e-9bc4-ecbb1f2b263f" />

---

## Quick start (no installation)

Run it instantly in the browser via Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/NikUrukalo/ZeroRisk-Trader/main?urlpath=proxy/8080/)

If the badge doesn't work, paste this into your address bar:

```
https://mybinder.org/v2/gh/NikUrukalo/ZeroRisk-Trader/main?urlpath=proxy/8080/
```

---

## Running it locally

### 1. Clone the repo

```bash
git clone https://github.com/NikUrukalo/ZeroRisk-Trader.git
cd ZeroRisk-Trader
```

> Run every command below from the project root.

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

| System | Command |
|---|---|
| Windows PowerShell | `venv\Scripts\Activate.ps1` |
| Windows CMD | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

The app connects to the faculty database as the shared `javnost` role, so no extra configuration is needed.

Open **http://localhost:8080** and stop the app anytime with `Ctrl+C`.

---

## Price refreshing

When anyone opens the login page, a price refresh starts **in the background**. `Services/price_service.py` reads the symbols from `asset_master`, downloads the latest prices from Yahoo Finance, converts them from USD to EUR, and writes a new snapshot into the `asset` table.

- At least 10 minutes must pass between two refreshes (`PRICE_REFRESH_SECONDS`).
- If Yahoo can't be reached, the error is only logged; the previous snapshot stays in the database and the app keeps working.

Because every run appends a new snapshot, a price history builds up over time — that's what powers the **Top 5 movers** list on the Trade page, which needs at least two snapshots to compare.

---

## The quiz

On the **Earn balance** page, users answer finance questions. A correct answer credits the question's reward to the portfolio; a wrong one credits nothing. After each attempt, a **one-hour cooldown** applies — measured with the database clock (`CURRENT_TIMESTAMP`) rather than the application's, so the calculation stays correct even on Binder, which runs in UTC.

---

## Data source

Prices come from [Yahoo Finance](https://finance.yahoo.com) via the `yfinance` library and are converted from USD to EUR at the rate of the moment they were scraped. These are delayed snapshots, not a live feed.

> NOTE: This is a student project for practicing database design. Nothing in it is investment advice, and no real money is involved.
