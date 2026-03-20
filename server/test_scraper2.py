import yfinance as yf
import pandas as pd
from datetime import datetime

def scrape_yahoo_history(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch 2 years of daily history, same as the app needs.
        history_df = stock.history(period="2y", interval="1d")
        
        if history_df.empty:
            return None
            
        data = []
        for date, row in history_df.iterrows():
            data.append({
                "Date": date.strftime('%Y-%m-%d'),
                "Open": float(row["Open"]),
                "High": float(row["High"]),
                "Low": float(row["Low"]),
                "Close": float(row["Close"]),
                "Adj Close": float(row.get("Adj Close", row["Close"])),
                "Volume": int(row["Volume"])
            })
            
        return data
    except Exception as e:
        print(f"yfinance error: {e}")
        return None

if __name__ == "__main__":
    res = scrape_yahoo_history("AAPL")
    if isinstance(res, list):
        print(f"Scraped {len(res)} rows using yfinance.")
        if len(res) > 0:
            print(res[-1]) # Print the most recent data
    else:
        print("Result:", res)
