import numpy as np

def minmax_scale(df, col, guidance="on"):
    df = df.copy()
    df[col + "_scaled"] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())

    if guidance == "on":
        print(f"📏 MinMax scaled '{col}'")

    return df


def standard_scale(df, col, guidance="on"):
    df = df.copy()
    df[col + "_scaled"] = (df[col] - df[col].mean()) / df[col].std()

    if guidance == "on":
        print(f"📐 Standard-scaled '{col}'")

    return df

def scale_numeric(df, cols, method="standard", guidance="on"):
    """
    Scale numeric columns.

    method:
    - standard
    - minmax
    """

    df = df.copy()

    if isinstance(cols, str):
        cols = [cols]

    if guidance == "on":
        print(f"📏 Scaling columns {cols} using '{method}'")

    for col in cols:
        if method == "standard":
            df = standard_scale(df, col, guidance="off")

        elif method == "minmax":
            df = minmax_scale(df, col, guidance="off")

        else:
            raise ValueError("Unknown scaling method")

    if guidance == "on":
        print("✨ Scaling complete.")

    return df
