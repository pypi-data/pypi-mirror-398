import pandas as pd


REQUIRED_COLUMNS = {"date", "time", "open", "high", "low", "close"}


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Combine date & time into datetime
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df


def split_by_day(df: pd.DataFrame) -> dict:
    days = {}

    for date, group in df.groupby(df["datetime"].dt.date):
        # Ignore incomplete days
        if len(group) < 10:
            continue

        days[str(date)] = group.reset_index(drop=True)

    return days
