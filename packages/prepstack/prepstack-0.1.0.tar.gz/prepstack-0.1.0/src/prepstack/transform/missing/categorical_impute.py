import pandas as pd

def categorical_impute(df, columns=None, method="mode", fill_value=None, guidance="off"):
    """
    Impute missing values in CATEGORICAL columns.

    method options:
    - "mode"
    - "constant"
    """

    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(exclude=["number"]).columns.tolist()

    if guidance == "on":
        print("🔤 CATEGORICAL IMPUTATION STARTED")
        print(f" • Columns: {columns}")
        print(f" • Strategy: {method}")

    for col in columns:
        if method == "mode":
            v = df[col].mode()[0]
        elif method == "constant":
            if fill_value is None:
                raise ValueError("fill_value must be provided for constant strategy")
            v = fill_value
        else:
            raise ValueError(f"Unknown method: {method}")

        if guidance == "on":
            print(f" → Filling NaN in '{col}' with '{v}'")

        df[col] = df[col].fillna(v)

    if guidance == "on":
        print("✨ Categorical imputation complete.")

    return df
