"""Background refresh of asset prices."""

import os
import threading
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation

from Data.repository import Repo

REFRESH_INTERVAL = int(os.environ.get('PRICE_REFRESH_SECONDS', 600))
BATCH_SIZE = 40

# Binder containers run on UTC, so every time the app printed was an hour or
# two behind Slovenian time. Timestamps are shown, and written, in this zone.
try:
    from zoneinfo import ZoneInfo
    APP_TZ = ZoneInfo(os.environ.get('APP_TIMEZONE', 'Europe/Ljubljana'))
except Exception:
    APP_TZ = None


def now():
    return datetime.now(APP_TZ)

_lock = threading.Lock()
_last_success = 0.0
_last_error = None
_running = False


def status():
    """What the Trade page shows about the last refresh."""
    with _lock:
        return {
            'running': _running,
            'last_success': (datetime.fromtimestamp(_last_success, APP_TZ)
                             if _last_success else None),
            'last_error': _last_error,
        }


def maybe_refresh(fetcher=None, force=False):
    """
    Start a refresh in the background if one is due.

    Returns immediately - the page never waits for it. Only a *successful*
    refresh resets the timer, so a failed attempt is retried on the next
    visit instead of being blocked for the whole interval.
    """
    global _running

    with _lock:
        if _running:
            return False
        if not force and (time.time() - _last_success) < REFRESH_INTERVAL:
            return False
        _running = True

    threading.Thread(target=_refresh, args=(fetcher,), daemon=True).start()
    return True


def _refresh(fetcher=None):
    global _running, _last_success, _last_error

    error = None
    stored = 0

    try:
        # A separate Repo: psycopg2 connections are not thread-safe and the
        # request handlers are using the shared one.
        repo = Repo()
        symbols = repo.get_all_asset_symbols()

        if not symbols:
            error = 'asset_master is empty'
        else:
            rows = _to_rows((fetcher or fetch_prices)(symbols))
            if rows:
                repo.insert_asset_prices(rows)
                stored = len(rows)
            else:
                error = 'no usable prices returned'

    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'

    with _lock:
        _running = False
        _last_error = error
        if not error:
            _last_success = time.time()

    print('[prices] ' + (f'stored {stored} prices' if not error
                         else f'failed: {error}'))


def _to_rows(prices):
    stamped = now()
    date_stamp = stamped.date()
    time_stamp = stamped.time().replace(microsecond=0)

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

        # Intraday first. A daily bar only moves once a day, so asking for
        # '1d' bars stored the same number on every refresh and the prices
        # looked frozen. One-minute bars move while a market is open, and
        # crypto moves around the clock.
        data = _download(yf, batch, period='1d', interval='1m')
        if data is None or getattr(data, 'empty', True):
            data = _download(yf, batch, period='5d', interval='1d')
        if data is None or getattr(data, 'empty', True):
            continue

        for symbol in batch:
            closes = _closes_for(data, symbol)
            if closes is None or closes.empty:
                continue
            prices[symbol] = float(closes.iloc[-1]) / rate

    return prices


def _download(yf, tickers, period, interval):
    try:
        return yf.download(tickers, period=period, interval=interval,
                           group_by='ticker', auto_adjust=True,
                           progress=False, threads=True)
    except Exception:
        return None


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
    data = _download(yf, 'EURUSD=X', period='5d', interval='1d')
    closes = _closes_for(data, 'EURUSD=X') if data is not None else None
    if closes is None or closes.empty:
        raise RuntimeError('could not read the EUR/USD rate')
    rate = float(closes.iloc[-1])
    if rate <= 0:
        raise RuntimeError('EUR/USD rate came back as zero')
    return rate
