"""
scraper.py — Yahoo Finance historical data scraper + technical indicator calculator
for the NexTrade / Stock Analytics feature in KodBank.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_stock_history(ticker: str) -> list[dict]:
    """
    Scrape Yahoo Finance historical data for the given ticker symbol.
    Returns a list of dicts with keys:
        Date, Open, High, Low, Close, Adj Close, Volume
    ordered oldest → newest.
    """
    url = f"https://finance.yahoo.com/quote/{ticker}/history/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch data for {ticker}: {exc}")

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise RuntimeError(f"No data table found for {ticker} on Yahoo Finance.")

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        # Only keep rows that have exactly 7 columns (skip Dividend/Split rows)
        if len(cells) != 7:
            continue
        rows.append({
            "Date":      cells[0],
            "Open":      cells[1],
            "High":      cells[2],
            "Low":       cells[3],
            "Close":     cells[4],
            "Adj Close": cells[5],
            "Volume":    cells[6],
        })

    # Yahoo returns newest first — reverse to chronological order
    rows.reverse()
    return rows


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Strip commas and convert to float, coercing errors to NaN."""
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def calculate_summary_statistics(history: list[dict]) -> dict:
    """
    Accept the list from fetch_stock_history(), convert to DataFrame,
    and return a dict containing summary stats + technical indicator values
    and their human-readable analysis strings.
    """
    df = pd.DataFrame(history)

    # Convert numeric columns
    for col in ["Open", "High", "Low", "Close", "Adj Close"]:
        df[col] = _clean_numeric(df[col])
    df["Volume"] = _clean_numeric(df["Volume"])

    df.dropna(subset=["Close"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    close   = df["Close"]
    price   = float(close.iloc[-1])   # latest closing price

    # ── Basic summary ────────────────────────────────────────────────────────
    first_close = float(close.iloc[0])
    price_change   = round(price - first_close, 4)
    percent_change = round((price_change / first_close) * 100, 4) if first_close else 0.0

    # ── RSI (14-period Wilder smoothing) ─────────────────────────────────────
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

    rs  = avg_gain / avg_loss.replace(0, float("inf"))
    rsi_series = 100 - (100 / (1 + rs))
    rsi_val = round(float(rsi_series.iloc[-1]), 2)

    if rsi_val > 70:
        rsi_analysis = "Asset is Overbought. Trend reversal may occur."
    elif rsi_val < 30:
        rsi_analysis = "Asset is Oversold. Potential buying opportunity."
    else:
        rsi_analysis = "RSI is Neutral."

    # ── Bollinger Bands (20-period, 2 std) ───────────────────────────────────
    bb_window = 20
    bb_mid    = close.rolling(window=bb_window).mean()
    bb_std    = close.rolling(window=bb_window).std()
    bb_upper_val = round(float(bb_mid.iloc[-1] + 2 * bb_std.iloc[-1]), 4)
    bb_lower_val = round(float(bb_mid.iloc[-1] - 2 * bb_std.iloc[-1]), 4)

    if price >= bb_upper_val:
        bb_analysis = "Price near Upper Band, suggesting overvalued."
    elif price <= bb_lower_val:
        bb_analysis = "Price near Lower Band, suggesting undervalued."
    else:
        bb_analysis = "Price within normal Bollinger Bands range."

    # ── Moving Averages ───────────────────────────────────────────────────────
    sma50  = round(float(close.rolling(window=50).mean().iloc[-1]),  4) if len(close) >= 50  else None
    sma200 = round(float(close.rolling(window=200).mean().iloc[-1]), 4) if len(close) >= 200 else None
    ema50  = round(float(close.ewm(span=50,  adjust=False).mean().iloc[-1]), 4)
    ema200 = round(float(close.ewm(span=200, adjust=False).mean().iloc[-1]), 4)

    if sma50 and sma200:
        if sma50 > sma200 and price > sma50:
            ma_analysis = "Strong Bullish Trend: Golden Cross."
        elif sma50 < sma200 and price < sma50:
            ma_analysis = "Strong Bearish Trend: Death Cross."
        elif price > sma200:
            ma_analysis = "Long-term Bullish."
        else:
            ma_analysis = "Long-term Bearish."
    elif price > (sma200 or ema200):
        ma_analysis = "Long-term Bullish."
    else:
        ma_analysis = "Long-term Bearish."

    # ── MACD (12, 26, 9) ─────────────────────────────────────────────────────
    ema12  = close.ewm(span=12, adjust=False).mean()
    ema26  = close.ewm(span=26, adjust=False).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist   = macd - signal

    macd_val   = round(float(macd.iloc[-1]),   4)
    signal_val = round(float(signal.iloc[-1]), 4)
    hist_val   = round(float(hist.iloc[-1]),   4)

    prev_macd   = float(macd.iloc[-2])   if len(macd)   >= 2 else macd_val
    prev_signal = float(signal.iloc[-2]) if len(signal) >= 2 else signal_val

    if prev_macd <= prev_signal and macd_val > signal_val:
        macd_analysis = "Bullish Crossover"
    elif prev_macd >= prev_signal and macd_val < signal_val:
        macd_analysis = "Bearish Crossover"
    elif macd_val > signal_val:
        macd_analysis = "Bullish Trend"
    elif macd_val < signal_val:
        macd_analysis = "Bearish Trend"
    else:
        macd_analysis = "Neutral"

    return {
        # Summary
        "last_close":     round(price, 4),
        "period_high":    round(float(df["High"].max()),  4),
        "period_low":     round(float(df["Low"].min()),   4),
        "average_close":  round(float(close.mean()),      4),
        "average_volume": round(float(df["Volume"].mean()), 2),
        "price_change":    price_change,
        "percent_change":  percent_change,
        "total_records":   len(df),
        # RSI
        "rsi":          rsi_val,
        "rsi_analysis": rsi_analysis,
        # Bollinger Bands
        "bb_upper":   bb_upper_val,
        "bb_lower":   bb_lower_val,
        "bb_analysis": bb_analysis,
        # Moving Averages
        "ma_50_sma":  sma50,
        "ma_200_sma": sma200,
        "ma_50_ema":  ema50,
        "ma_200_ema": ema200,
        "ma_analysis": ma_analysis,
        # MACD
        "macd_line":   macd_val,
        "macd_signal": signal_val,
        "macd_hist":   hist_val,
        "macd_analysis": macd_analysis,
    }
