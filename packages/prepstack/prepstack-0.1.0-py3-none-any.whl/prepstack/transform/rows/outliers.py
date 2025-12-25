import pandas as pd

def iqr_outliers(df, column, guidance="on"):
    df = df.copy()

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df["is_outlier"] = ~df[column].between(lower, upper)

    if guidance == "on":
        print(f"🚨 IQR Outlier detection on '{column}'")
        print(f" • Lower bound = {lower:.2f}")
        print(f" • Upper bound = {upper:.2f}")
        print(f" • Outliers found: {df['is_outlier'].sum()}")

    return df
