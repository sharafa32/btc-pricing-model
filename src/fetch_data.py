"""Fetch every factor in src/factors.py from Newhedge."""
import os
import time
import sys
import requests
import pandas as pd
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from factors import FACTORS

load_dotenv()
API_TOKEN = os.getenv("NEWHEDGE_API_KEY")
if not API_TOKEN:
    raise ValueError("NEWHEDGE_API_KEY not found in .env")

BASE_URL = "https://newhedge.io/api/v2/metrics"
RAW_DIR = "data/raw"

def fetch_metric(chart_slug, metric_name, column_name):
    url = f"{BASE_URL}/{chart_slug}/{metric_name}"
    params = {"api_token": API_TOKEN}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp_ms", column_name])
    df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
    df = df[["date", column_name]].set_index("date")
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    return df

def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    successes, failures = [], []
    for factor in FACTORS:
        name = factor["name"]
        try:
            print(f"Fetching {name}... ", end="", flush=True)
            df = fetch_metric(factor["chart_slug"], factor["metric_name"], name)
            df.to_csv(os.path.join(RAW_DIR, f"{name}.csv"))
            print(f"OK ({df.shape[0]} rows)")
            successes.append(name)
        except Exception as e:
            print(f"FAILED ({type(e).__name__})")
            failures.append(name)
        time.sleep(1.0)
    print(f"\nSucceeded: {len(successes)}/{len(FACTORS)}")
    if failures: print(f"Failed: {failures}")

if __name__ == "__main__":
    main()