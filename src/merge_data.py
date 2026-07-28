"""Merge all raw CSVs into a single daily DataFrame."""
import os
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def main():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]
    print(f"Found {len(files)} raw CSVs to merge.")

    # Load all CSVs into a list of DataFrames
    dfs = []
    for f in files:
        name = f.replace(".csv", "")
        df = pd.read_csv(os.path.join(RAW_DIR, f), index_col="date", parse_dates=True)
        # Handle potential duplicate dates by taking the last value
        df = df[~df.index.duplicated(keep='last')]
        dfs.append(df)

    # Merge all DataFrames on the index (date) using outer join
    print("Merging...")
    merged = pd.concat(dfs, axis=1)
    
    # Filter to 2015-01-01 forward (filters out noisy early BTC data)
    merged = merged.loc["2015-01-01":]
    
    # Create a complete daily index (including weekends) and forward-fill macro data
    # This handles FRED weekly data and any missing days
    daily_index = pd.date_range(start=merged.index.min(), end=merged.index.max(), freq="D")
    merged = merged.reindex(daily_index)
    
    # Forward-fill macro/sentiment data (liquidity, yields, trends) up to 7 days
    # DO NOT forward-fill on-chain data (those are strictly daily)
    macro_cols = ["global_liquidity_t", "treasury_10y", "google_trends_btc"]
    for col in macro_cols:
        if col in merged.columns:
            merged[col] = merged[col].ffill(limit=7)

    # Save to processed folder
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    output_path = os.path.join(PROCESSED_DIR, "factors_daily.csv")
    merged.to_csv(output_path)
    
    print(f"\nMerge complete! Saved to {output_path}")
    print(f"Final Dataset Shape: {merged.shape}")
    print(f"Date Range: {merged.index.min().date()} to {merged.index.max().date()}")

if __name__ == "__main__":
    main()