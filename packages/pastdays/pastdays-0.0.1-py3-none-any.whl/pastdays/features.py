import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame, window_minutes: int) -> np.ndarray:
    """
    Extract features from first N minutes of the day.
    """

    df_window = df.iloc[:window_minutes]

    open_price = df_window.iloc[0]["open"]
    close_price = df_window.iloc[-1]["close"]
    high_price = df_window["high"].max()
    low_price = df_window["low"].min()

    gap_pct = 0.0  # v0: optional later
    range_pct = (high_price - low_price) / open_price * 100
    direction = 1 if close_price > open_price else -1

    returns = df_window["close"].pct_change().dropna()
    volatility = returns.std() * 100 if not returns.empty else 0.0

    return np.array([
        gap_pct,
        range_pct,
        direction,
        volatility
    ])
