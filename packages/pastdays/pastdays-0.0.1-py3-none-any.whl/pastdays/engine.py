import numpy as np
from .loader import load_csv, split_by_day
from .features import build_features
from .similarity import rank_similar_days
from .report import Report


class SimilarDayEngine:

    def __init__(self, historical_data: str, window_minutes: int = 30):
        self.window_minutes = window_minutes

        df = load_csv(historical_data)
        self.historical_days = split_by_day(df)

        self.history_features = {
            date: build_features(day_df, window_minutes)
            for date, day_df in self.historical_days.items()
        }

    def match(
        self,
        current_data: str,
        k: int = 15,
        lookahead_minutes: int = 180
    ):
        current_df = load_csv(current_data)
        current_features = build_features(current_df, self.window_minutes)

        ranked = rank_similar_days(current_features, self.history_features)
        top_days = ranked[:k]

        outcomes = []

        for date, _ in top_days:
            day_df = self.historical_days[date]

            if len(day_df) <= self.window_minutes + lookahead_minutes:
                continue

            start_price = day_df.iloc[self.window_minutes]["close"]
            end_df = day_df.iloc[
                self.window_minutes:self.window_minutes + lookahead_minutes
            ]

            max_up = (end_df["high"].max() - start_price) / start_price * 100
            max_down = (end_df["low"].min() - start_price) / start_price * 100
            final_move = (end_df.iloc[-1]["close"] - start_price) / start_price * 100

            outcomes.append({
                "date": date,
                "max_up": max_up,
                "max_down": max_down,
                "final_move": final_move
            })

        return Report(outcomes, k, lookahead_minutes)
