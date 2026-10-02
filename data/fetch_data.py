import os
import pandas as pd
import yfinance as yf
from mftool import Mftool

# Define output directory
RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

# AMFI Scheme Codes for representative asset classes
SCHEMES = {
    "equity": "119598",   # Nippon India Large Cap Fund - Direct Plan - Growth
    "debt": "118989",     # HDFC Short Term Debt Fund - Direct Plan - Growth
    "hybrid": "120166",   # ICICI Prudential Balanced Advantage Fund - Direct Plan - Growth
    "liquid": "119551",   # Aditya Birla Sun Life Liquid Fund - Direct Plan - Growth
}

BENCHMARK_TICKER = "^NSEI"  # NIFTY 50
START_DATE = "2018-01-01"
END_DATE = "2025-12-31"

def fetch_amfi_navs():
    """Fetch historical NAV time series using mftool."""
    mf = Mftool()
    nav_frames = {}

    for category, code in SCHEMES.items():
        print(f"Fetching NAV for {category.upper()} (Scheme Code: {code})...")
        try:
            data = mf.get_scheme_historical_nav(code, as_Dataframe=True)
            if data is not None and not data.empty:
                # mftool returns 'nav' column with date index (DD-MM-YYYY)
                df = data[["nav"]].rename(columns={"nav": f"{category}_nav"})
                df.index = pd.to_datetime(df.index, format="%d-%m-%Y")
                df[f"{category}_nav"] = pd.to_numeric(df[f"{category}_nav"], errors="coerce")
                nav_frames[category] = df
            else:
                print(f"Warning: No data returned for {category} ({code})")
        except Exception as e:
            print(f"Error fetching {category} ({code}): {e}")

    # Merge all mutual fund categories on Date
    if nav_frames:
        combined_mf = pd.concat(nav_frames.values(), axis=1, join="outer").sort_index()
        combined_mf = combined_mf.loc[START_DATE:END_DATE]
        mf_path = os.path.join(RAW_DATA_DIR, "mf_nav_raw.csv")
        combined_mf.to_csv(mf_path)
        print(f"Saved Mutual Fund NAVs to {mf_path}")
        return combined_mf
    return None

def fetch_benchmark():
    """Fetch NIFTY 50 index data from Yahoo Finance."""
    print(f"Fetching benchmark data for {BENCHMARK_TICKER}...")
    nifty = yf.download(BENCHMARK_TICKER, start=START_DATE, end=END_DATE, progress=False)
    
    # Handle MultiIndex columns if returned by newer yfinance versions
    if isinstance(nifty.columns, pd.MultiIndex):
        nifty.columns = [col[0] for col in nifty.columns]

    nifty = nifty[["Open", "High", "Low", "Close", "Volume"]].rename(
        columns={
            "Open": "nifty_open",
            "High": "nifty_high",
            "Low": "nifty_low",
            "Close": "nifty_close",
            "Volume": "nifty_volume",
        }
    )
    nifty.index = pd.to_datetime(nifty.index)
    nifty_path = os.path.join(RAW_DATA_DIR, "nifty_raw.csv")
    nifty.to_csv(nifty_path)
    print(f"Saved NIFTY 50 data to {nifty_path}")
    return nifty

if __name__ == "__main__":
    print("Starting data ingestion...")
    fetch_amfi_navs()
    fetch_benchmark()
    print("Data ingestion complete.")