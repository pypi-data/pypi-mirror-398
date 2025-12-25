import pandas as pd

def bin_equal_width(df, col, bins=4, labels=None, guidance="on"):
    """Equal-width binning."""
    df = df.copy()
    df[col + "_bin"] = pd.cut(df[col], bins=bins, labels=labels)

    if guidance == "on":
        print(f"📦 Equal-width binning applied to '{col}' with {bins} bins")

    return df


def bin_equal_freq(df, col, bins=4, labels=None, guidance="on"):
    """Equal-frequency binning."""
    df = df.copy()
    df[col + "_bin"] = pd.qcut(df[col], q=bins, labels=labels)

    if guidance == "on":
        print(f"📊 Equal-frequency binning applied to '{col}' with {bins} bins")

    return df


def bin_custom(df, col, ranges, labels=None, guidance="on"):
    """Custom binning with ranges."""
    df = df.copy()
    df[col + "_bin"] = pd.cut(df[col], bins=ranges, labels=labels, include_lowest=True)

    if guidance == "on":
        print(f"🎨 Custom binning applied to '{col}' with ranges {ranges}")

    return df
