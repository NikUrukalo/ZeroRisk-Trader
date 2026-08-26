# ZeroRisk Trader

ZeroRisk Trader is a fun web application for practising stock, ETF and crypto trading with **virtual
money**. Real market prices, a real relational database, and nothing at stake.

Project for **Osnove podatkovnih baz** (FMF, 2026).

**Authors:** Nejc Žibret and Nik Urukalo

---

## What the application does

You register, and you get a virtual portfolio. Prices for around 200 assets are
scraped from Yahoo Finance into a PostgreSQL database on the faculty server, and
every order is priced against the latest stored snapshot.

| Page | What it does |
|---|---|
| **Login / Register** | Passwords are stored as bcrypt hashes, the session runs on a cookie. Opening the login page also kicks off a price refresh in the background. |
| **Overview** | Cash balance, value of holdings, total portfolio value, every open position with its profit or loss, and the ten most recent trades. |
| **Trade** | Every asset with its latest price, live search by name or symbol, buying and selling of any (also fractional) quantity, and the five biggest movers. |
| **Earn balance** | A finance quiz. A correct answer credits the reward to your balance, then a one-hour cooldown applies. |

---

## ER Diagram:
<img width="2146" height="870" alt="ZeroRisk_Trader drawio (1)" src="https://github.com/user-attachments/assets/87799eb9-41e5-424e-9bc4-ecbb1f2b263f" />

The database has **eight tables**:

| Table | Meaning |
|---|---|
| `app_user` | user accounts, with bcrypt password hashes |
| `portfolio` | the user's wallet and virtual cash balance |
| `asset_master` | the catalogue: symbol, name and type (Stock / ETF / Crypto) |
| `asset` | price history, one row per (symbol, moment it was scraped) |
| `trade` | log of every buy and sell |
| `position` | the current holding per asset, with its average buy price |
| `trivia_question` | the quiz bank and the reward for each question |
| `trivia_attempt` | who answered what, when, and whether it was correct |

---

## Project structure

```
ZeroRisk-Trader/
├── app.py                       routes
├── bottleext.py                 url(), redirect() and template() for Bottle
├── requirements.txt
│
├── Data/                        DATA LAYER
│   ├── auth_public.py             database connection settings
│   ├── models.py                  data models (dataclass)
│   ├── repository.py              every SQL query in the project
│   ├── create_database.sql        the schema
│   ├── grants.sql                 privileges for the `javnost` role
│   ├── trivia_questions.sql       quiz questions
│   └── Data scraping/             price download from Yahoo Finance
│
├── Services/                    BUSINESS LAYER
│   ├── auth_service.py            registration, login, bcrypt
│   ├── trading_services.py        portfolio, buying, selling, quiz
│   └── price_service.py           background price refresh
│
├── Presentation/                WEB LAYER
│   ├── static/style.css           navy and gray theme
│   └── views/                     HTML templates
│
└── binder/                      configuration for mybinder.org
```

The application is split into three layers, and each one only talks to the one
below it:

```
app.py  →  Services/  →  Data/repository.py  →  PostgreSQL
```

`app.py` contains no SQL and `Services/` never talks to the database directly,
so a change to the schema only touches `repository.py`.

---

## Running it on Binder

The easiest way, with nothing to install:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/NikUrukalo/ZeroRisk-Trader/main?urlpath=proxy/8080/)

If the badge does not work, paste this into the address bar:

```
https://mybinder.org/v2/gh/NikUrukalo/ZeroRisk-Trader/main?urlpath=proxy/8080/
```

The first launch builds the image and takes a few minutes; later launches are
cached and start in seconds.

Three settings in `binder/` are the reason this works at all:

* **`BOTTLE_ROOT`** — on Binder the app is not served from the root of the
  domain but from `/user/<id>/proxy/8080/`. `url()` prepends that prefix to
  every link; without it every link, form and stylesheet returns 404.
* **`POSTGRES_PORT=443`** — Binder only allows outbound connections on ports 80
  and 443. PostgreSQL's usual 5432 does not fail fast, it hangs until the
  connection times out. `baza.fmf.uni-lj.si` also listens on 443.
* **redirects go out as absolute URLs** — jupyter-server-proxy 4.5 and newer
  prepend the proxy prefix to relative `Location` headers, so a redirect that
  already contained the prefix ended up with it twice. See `bottleext.redirect`.

---

## Running it locally

### 1. Clone

```bash
git clone https://github.com/NikUrukalo/ZeroRisk-Trader.git
cd ZeroRisk-Trader
```

Run every command below from the project root.

### 2. Virtual environment

```bash
python -m venv venv
```

Activate it:

| System | Command |
|---|---|
| Windows PowerShell | `venv\Scripts\Activate.ps1` |
| Windows CMD | `venv\Scripts\activate.bat` |
| macOS / Linux | `source venv/bin/activate` |

### 3. Install the libraries

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run

```bash
python app.py
```

Open **<http://localhost:8080>**. Stop with `Ctrl+C`.

The app connects to the faculty database as the shared `javnost` role, so no
configuration is needed.

### 5. Preparing the database (first time only)

If the tables do not exist yet, create them as the **owner** of the database
(your personal FMF account — `javnost` may not create tables):

```bash
psql -h baza.fmf.uni-lj.si -U <your_account> -d sem2026_nejczi -f Data/create_database.sql
psql -h baza.fmf.uni-lj.si -U <your_account> -d sem2026_nejczi -f Data/grants.sql
psql -h baza.fmf.uni-lj.si -U <your_account> -d sem2026_nejczi -f Data/trivia_questions.sql
```

Then fill the asset catalogue:

```bash
cd "Data scraping"
python fill_asset_master.py
python fill_asset.py
```

---

## Price refreshing

When anyone opens the login page, a price refresh starts **in the background**:
`Services/price_service.py` reads the symbols from `asset_master`, downloads the
latest prices from Yahoo Finance, converts them from dollars to euros and writes
a new snapshot into the `asset` table.

* The page never waits for it — it renders in a few milliseconds.
* At least 10 minutes must pass between two refreshes (`PRICE_REFRESH_SECONDS`).
* If Yahoo cannot be reached the error is only logged; the previous snapshot
  stays in the database and the app keeps working.

Because every run appends a new snapshot, a price history builds up over time.
That is what makes the "Top 5 movers" list on the **Trade** page work — it needs
at least two snapshots to compare.

---

## The quiz

On **Earn balance** the user answers finance questions. A correct answer credits
the question's reward to the portfolio; a wrong one credits nothing. After each
attempt a **one-hour cooldown** applies, measured with the database clock
(`CURRENT_TIMESTAMP`) rather than the application's — otherwise the calculation
would be two hours out on Binder, which runs in UTC.

---

## Data source

Prices come from [Yahoo Finance](https://finance.yahoo.com) through the
`yfinance` library and are converted from USD to EUR at the rate of the moment
they were scraped. They are delayed snapshots, not a live feed. This is a
student project for practising database design — nothing in it is investment
advice and no real money is involved.
