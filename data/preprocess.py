
import os
import numpy as np
import pandas as pd
import ta

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(__file__), "processed")
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

MF_PATH = os.path.join(RAW_DATA_DIR, "mf_nav_raw.csv")
NIFTY_PATH = os.path.join(RAW_DATA_DIR, "nifty_raw.csv")
OUTPUT_PATH = os.path.join(
    PROCESSED_DATA_DIR, "processed_market_data_v2.parquet"
)

ASSETS = ["equity", "debt", "hybrid", "liquid"]


def load_and_align_datasets():
    if not os.path.exists(MF_PATH) or not os.path.exists(NIFTY_PATH):
        raise FileNotFoundError(
            "Raw CSV files missing. Run data/fetch_data.py first."
        )

    df_mf = pd.read_csv(MF_PATH, index_col=0, parse_dates=True)
    df_nifty = pd.read_csv(NIFTY_PATH, index_col=0, parse_dates=True)

    df_combined = pd.merge(
        df_mf,
        df_nifty,
        left_index=True,
        right_index=True,
        how="outer",
    )

    df_combined = df_combined.sort_index()

    if df_combined.index.has_duplicates:
        raise ValueError("Duplicate dates found in market data.")

    required = [f"{asset}_nav" for asset in ASSETS] + ["nifty_close"]

    for column in required:
        if column not in df_combined.columns:
            raise ValueError(f"Missing required column: {column}")

        df_combined[column] = pd.to_numeric(
            df_combined[column], errors="coerce"
        )

    # Forward-fill only: never use future values to fill past dates.
    df_aligned = df_combined[required].ffill()

    # Remove dates before all required prices become available.
    df_aligned = df_aligned.dropna(subset=required)

    if not np.isfinite(df_aligned[required].to_numpy()).all():
        raise ValueError("Non-finite market prices detected.")

    if (df_aligned[required] <= 0).any().any():
        raise ValueError("Market prices must be positive.")

    return df_aligned


def engineer_features(df: pd.DataFrame):
    data = df.copy()

    # Simple daily returns, compatible with portfolio_value * (1 + return)
    for asset in ASSETS:
        nav_col = f"{asset}_nav"
        ret_col = f"{asset}_return"

        data[ret_col] = data[nav_col].pct_change(fill_method=None)

        data[f"{asset}_vol_30d"] = (
            data[ret_col].rolling(30).std() * np.sqrt(252)
        )
        data[f"{asset}_vol_90d"] = (
            data[ret_col].rolling(90).std() * np.sqrt(252)
        )

    data["nifty_return"] = data["nifty_close"].pct_change(
        fill_method=None
    )

    data["nifty_vol_30d"] = (
        data["nifty_return"].rolling(30).std() * np.sqrt(252)
    )

    data["nifty_rsi_14"] = (
        ta.momentum.rsi(data["nifty_close"], window=14) / 100.0
    )

    sma_20 = ta.trend.sma_indicator(data["nifty_close"], window=20)
    sma_50 = ta.trend.sma_indicator(data["nifty_close"], window=50)

    data["nifty_sma_ratio"] = (sma_20 / sma_50) - 1.0

    macd = ta.trend.MACD(data["nifty_close"])
    data["nifty_macd_diff"] = (
        macd.macd_diff() / data["nifty_close"]
    )

    data = data.replace([np.inf, -np.inf], np.nan).dropna().copy()

    if len(data) < 2:
        raise ValueError("Not enough valid rows after preprocessing.")

    return data


def main():
    print("Loading and aligning market data...")
    aligned_df = load_and_align_datasets()

    print("Generating financial features...")
    processed_df = engineer_features(aligned_df)

    print(f"Processed rows: {len(processed_df)}")
    print(f"Features generated: {len(processed_df.columns)}")

    processed_df.to_parquet(OUTPUT_PATH, engine="pyarrow")

    print(f"Saved dataset to: {OUTPUT_PATH}")
    print("Preprocessing completed successfully!")


if __name__ == "__main__":
    main()
