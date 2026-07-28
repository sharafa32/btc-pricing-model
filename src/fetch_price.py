"""Fetch BTC historical price (separate API from metrics)."""
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("NEWHEDGE_API_KEY")
if not API_TOKEN:
    raise ValueError("NEWHEDGE_API_KEY not found in .env")

url = "https://newhedge.io/api/v2/price/historical"
params = {"api_token": API_TOKEN}
response = requests.get(url, params=params, timeout=30)
print(f"Status: {response.status_code}")
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data, columns=["timestamp_ms", "btc_price"])
df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
df = df[["date", "btc_price"]].set_index("date")
df.to_csv("data/raw/btc_price.csv")
print(f"Saved btc_price: {df.shape[0]} rows")