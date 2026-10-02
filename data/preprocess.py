import os
import numpy as np
import pandas as pd
import ta

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), "processed")
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

MF_PATH = os.path.join(RAW_DATA_DIR, "mf_nav_raw.csv")
NIFTY_PATH = os.path.join(RAW_DATA_DIR, "nifty_raw.csv")
OUTPUT_PATH = os.path.join(PROCESSED_DATA_DIR, "processed_market_data.parquet")

def load_and_align_datasets():
    """Load raw CSVs, align dates, and forward-fill non-trading day gaps."""
    if not os.path.exists(MF_PATH) or not os.path.exists(NIFTY_PATH):
        raise FileNotFoundError("Raw data files not found in data/raw/. Run fetch_data.py first.")

    # Load data with DatetimeIndex
    df_mf = pd.read_csv(MF_PATH, index_col=0, parse_dates=True)
    df_nifty = pd.read_csv(NIFTY_PATH, index_col=0, parse_dates=True)

    # Inner/Outer merge based on date
    df_combined = pd.merge(df_mf, df_nifty, left_index=True, right_index=True, how="outer")

    # Resample to NSE Trading Business Days (drop non-trading weekends/holidays)
    # Forward-fill missing values (e.g. if a fund NAV update was delayed by 1 day)
    df_aligned = df_combined.sort_index().ffill().bfill()

    # Drop any remaining non-trading days where Nifty has no volume/close
    df_aligned = df_aligned[df_aligned["nifty_close"].notna()]

    return df_aligned

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily returns, rolling volatilities, and technical indicators."""
    data = df.copy()

    asset_classes = ["equity", "debt", "hybrid", "liquid"]

    # 1. Compute Daily Log Returns for each fund class
    for asset in asset_classes:
        nav_col = f"{asset}_nav"
        ret_col = f"{asset}_return"
        data[ret_col] = np.log(data[nav_col] / data[nav_col].shift(1))

        # 30-day and 90-day annualized rolling volatility (252 trading days)
        data[f"{asset}_vol_30d"] = data[ret_col].rolling(window=30).std() * np.sqrt(252)
        data[f"{asset}_vol_90d"] = data[ret_col].rolling(window=90).std() * np.sqrt(252)

    # 2. Compute Benchmark (NIFTY 50) Indicators
    data["nifty_return"] = np.log(data["nifty_close"] / data["nifty_close"].shift(1))
    data["nifty_vol_30d"] = data["nifty_return"].rolling(window=30).std() * np.sqrt(252)

    # Momentum / Trend: RSI (14 days)
    data["nifty_rsi_14"] = ta.momentum.rsi(data["nifty_close"], window=14) / 100.0  # Normalize to [0, 1]

    # Moving Average Ratios (SMA 20 vs SMA 50)
    sma_20 = ta.trend.sma_indicator(data["nifty_close"], window=20)
    sma_50 = ta.trend.sma_indicator(data["nifty_close"], window=50)
    data["nifty_sma_ratio"] = (sma_20 / sma_50) - 1.0  # Percentage spread

    # MACD normalized
    macd = ta.trend.MACD(data["nifty_close"])
    data["nifty_macd_diff"] = macd.macd_diff() / data["nifty_close"]

    # Drop initial rolling window warmup NaNs
    data = data.dropna().copy()
    return data

def main():
    print("Aligning datasets...")
    aligned_df = load_and_align_datasets()
    print(f"Total raw aligned rows: {len(aligned_df)}")

    print("Computing rolling financial indicators & features...")
    processed_df = engineer_features(aligned_df)
    print(f"Total processed rows (post-warmup): {len(processed_df)}")

    # Save to Parquet for fast I/O during RL training
    processed_df.to_parquet(OUTPUT_PATH, engine="pyarrow")
    print(f"Saved preprocessed dataset to: {OUTPUT_PATH}")
    print("\nFeature Columns Generated:")
    for col in processed_df.columns:
        print(f" - {col}")

if __name__ == "__main__":
    main()