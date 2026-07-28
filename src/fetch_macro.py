"""Fetch Macro & Sentiment data (FRED and Google Trends)."""
import os
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred
from pytrends.request import TrendReq

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY not found in .env")

# 1. Pull Global Liquidity (WALCL = Fed Balance Sheet in millions, divide by 1e6 for trillions)
print("Fetching Global Liquidity (FRED)...")
fred = Fred(api_key=FRED_API_KEY)
liquidity = fred.get_series('WALCL')
liquidity = (liquidity / 1e6).to_frame("global_liquidity_t") # Convert to Trillions
liquidity.index.name = "date"
liquidity.to_csv("data/raw/global_liquidity.csv")
print(f"Saved global_liquidity: {len(liquidity)} rows")
# 2. Pull Google Trends for "Bitcoin" (Daily from 2015)
print("Fetching Google Trends (Bitcoin)...")
pytrends = TrendReq(hl='en-US', tz=360)
# Use specific date range to force daily granularity
pytrends.build_payload(['Bitcoin'], cat=0, timeframe='2015-01-01 2024-12-31', geo='', gprop='')
trends = pytrends.interest_over_time()
if 'isPartial' in trends.columns:
    trends = trends.drop(columns=['isPartial'])
trends.columns = ["google_trends_btc"]
trends.index.name = "date"
trends.to_csv("data/raw/google_trends.csv")
print(f"Saved google_trends: {len(trends)} rows")