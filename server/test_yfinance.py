import sys
import os

# Add server directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import fetch_stock_history, calculate_summary_statistics

if __name__ == "__main__":
    ticker = "AAPL"
    print(f"Fetching data for {ticker}...")
    try:
        history = fetch_stock_history(ticker)
        print(f"Got {len(history)} records. First record: {history[0]}")
        
        stats = calculate_summary_statistics(history)
        print("\nStatistics:")
        for k, v in stats.items():
            print(f"{k}: {v}")
            
    except Exception as e:
        print(f"Error: {e}")
