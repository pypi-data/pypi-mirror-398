import pandas as pd

def mixed_impute(df, numeric_method="median", cat_method="mode", guidance="off"):
    """
    Automatically imputes numeric and categorical columns using separate rules.
    """

    df = df.copy()

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    if guidance == "on":
        print("🤖 MIXED IMPUTATION STARTED")
        print(f" • Numeric columns: {numeric_cols}")
        print(f" • Categorical columns: {categorical_cols}")
        print(f" • Strategies: numeric={numeric_method}, categorical={cat_method}")

    # Numeric
    for col in numeric_cols:
        if numeric_method == "mean":
            v = df[col].mean()
        elif numeric_method == "median":
            v = df[col].median()
        elif numeric_method == "min":
            v = df[col].min()
        elif numeric_method == "max":
            v = df[col].max()
        else:
            raise ValueError("Invalid numeric method")

        df[col] = df[col].fillna(v)
        if guidance == "on":
            print(f" → {col}: filled with {v}")

    # Categorical
    for col in categorical_cols:
        if cat_method == "mode":
            v = df[col].mode()[0]
        else:
            raise ValueError("Invalid categorical method")

        df[col] = df[col].fillna(v)
        if guidance == "on":
            print(f" → {col}: filled with '{v}'")

    if guidance == "on":
        print("✨ Mixed imputation complete.")

    return df
