import pandas as pd

def extract_date_parts(df, col, guidance="on"):
    df = df.copy()
    df[col] = pd.to_datetime(df[col], errors="coerce")

    df[col + "_year"] = df[col].dt.year
    df[col + "_month"] = df[col].dt.month
    df[col + "_day"] = df[col].dt.day
    df[col + "_weekday"] = df[col].dt.weekday

    if guidance == "on":
        print(f"📅 Extracted date parts from '{col}'")

    return df


def date_diff(df, start_col, end_col, new_col="date_diff", guidance="on"):
    df = df.copy()

    df[start_col] = pd.to_datetime(df[start_col], errors="coerce")
    df[end_col] = pd.to_datetime(df[end_col], errors="coerce")

    df[new_col] = (df[end_col] - df[start_col]).dt.days

    if guidance == "on":
        print(f"⏳ Date difference '{new_col}' created from '{start_col}' → '{end_col}'")

    return df
