"""Background refresh of asset prices."""

import os
import threading
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation

from Data.repository import Repo

REFRESH_INTERVAL = int(os.environ.get('PRICE_REFRESH_SECONDS', 600))
BATCH_SIZE = 40

_lock = threading.Lock()
_last_refresh = 0.0
_running = False


def maybe_refresh(fetcher=None):
    """
    Start a price refresh in the background if one is due.

    Returns immediately - the caller (the login page) never waits for it.
    """
    global _last_refresh, _running

    with _lock:
        if _running or (time.time() - _last_refresh) < REFRESH_INTERVAL:
            return False
        _running = True
        _last_refresh = time.time()

    threading.Thread(target=_refresh, args=(fetcher,), daemon=True).start()
    return True


def _refresh(fetcher=None):
    global _running

    try:
        # A separate Repo, because psycopg2 connections are not thread-safe
        # and the request handlers are using the shared one.
        repo = Repo()
        symbols = repo.get_all_asset_symbols()

        if not symbols:
            print('[prices] asset_master is empty, nothing to refresh')
            return

        prices = (fetcher or fetch_prices)(symbols)
        rows = _to_rows(prices)

        if rows:
            repo.insert_asset_prices(rows)
            print(f'[prices] stored {len(rows)} prices')
        else:
            print('[prices] no usable prices returned')

    except Exception as exc:
        # A failed refresh must never take the site down; the previous
        # snapshot stays in the database and the app keeps working.
        print(f'[prices] refresh failed: {exc}')

    finally:
        with _lock:
            _running = False


def _to_rows(prices):
    now = datetime.now()
    date_stamp = now.date()
    time_stamp = now.time().replace(microsecond=0)

    rows = []
    for symbol, value in (prices or {}).items():
        try:
            price = Decimal(str(value)).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if price > 0:
            rows.append((symbol, price, date_stamp, time_stamp))
    return rows


def fetch_prices(symbols):
    """{symbol: price in EUR} from Yahoo Finance."""
    import yfinance as yf

    rate = _usd_per_eur(yf)
    prices = {}

    for start in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[start:start + BATCH_SIZE]
        data = yf.download(batch, period='1d', interval='1d',
                           group_by='ticker', auto_adjust=True,
                           progress=False, threads=True)
        if data is None or data.empty:
            continue

        for symbol in batch:
            closes = _closes_for(data, symbol)
            if closes is None or closes.empty:
                continue
            prices[symbol] = float(closes.iloc[-1]) / rate

    return prices


def _closes_for(frame, symbol):
    """yfinance lays the columns out differently for one vs many tickers."""
    for getter in (lambda: frame[symbol]['Close'],
                   lambda: frame['Close'][symbol],
                   lambda: frame['Close']):
        try:
            closes = getter()
        except (KeyError, TypeError, IndexError):
            continue
        if hasattr(closes, 'squeeze'):
            closes = closes.squeeze()
        if hasattr(closes, 'dropna'):
            return closes.dropna()
    return None


def _usd_per_eur(yf):
    data = yf.download('EURUSD=X', period='5d', progress=False)['Close'].dropna()
    rate = float(data.iloc[-1])
    return rate if rate > 0 else 1.0
