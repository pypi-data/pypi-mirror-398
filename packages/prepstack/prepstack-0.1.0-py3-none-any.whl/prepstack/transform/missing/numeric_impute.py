import pandas as pd

def numeric_impute(df, columns=None, method="mean", fill_value=None, guidance="off"):
    """
    Impute missing values in NUMERIC columns.

    method options:
    - "mean"
    - "median"
    - "min"
    - "max"
    - "constant"
    """

    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(include=["number"]).columns.tolist()

    if guidance == "on":
        print("🔢 NUMERIC IMPUTATION STARTED")
        print(f" • Columns: {columns}")
        print(f" • Strategy: {method}")

    for col in columns:
        if method == "mean":
            v = df[col].mean()
        elif method == "median":
            v = df[col].median()
        elif method == "min":
            v = df[col].min()
        elif method == "max":
            v = df[col].max()
        elif method == "constant":
            if fill_value is None:
                raise ValueError("fill_value must be provided for constant strategy")
            v = fill_value
        else:
            raise ValueError(f"Unknown method: {method}")

        if guidance == "on":
            print(f" → Filling NaN in '{col}' with {v}")

        df[col] = df[col].fillna(v)

    if guidance == "on":
        print("✨ Numeric imputation complete.")

    return df
