import yfinance as yf
import pandas as pd
import time

def download_assets(tickers, batch_size=25, period="1mo", interval="1d", pause=2):
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