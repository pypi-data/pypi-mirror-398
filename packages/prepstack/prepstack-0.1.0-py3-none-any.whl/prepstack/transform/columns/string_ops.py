import pandas as pd

def strip_whitespace(df, columns=None, guidance="off"):
    """
    Remove leading/trailing whitespace from string columns.
    """
    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(include=["object"]).columns.tolist()

    if guidance == "on":
        print("✨ STRING WHITESPACE CLEANING STARTED")
        print(f" • Columns: {columns}")

    for col in columns:
        df[col] = df[col].astype(str).str.strip()
        if guidance == "on":
            print(f" → Stripped whitespace from '{col}'")

    if guidance == "on":
        print("✨ Whitespace cleaning complete.\n")

    return df


def to_lower(df, columns=None, guidance="off"):
    """
    Convert string columns to lowercase.
    """
    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(include=["object"]).columns.tolist()

    if guidance == "on":
        print("🔡 LOWERCASE TRANSFORMATION STARTED")
        print(f" • Columns: {columns}")

    for col in columns:
        df[col] = df[col].astype(str).str.lower()
        if guidance == "on":
            print(f" → Converted '{col}' to lowercase")

    if guidance == "on":
        print("✨ Lowercase transformation complete.\n")

    return df

import pandas as pd

def clean_strings(
    df,
    columns,
    strip=True,
    lower=True,
    upper=False,
    guidance="on"
):
    """
    Apply common string cleaning operations in one step.

    Options:
    - strip: remove leading/trailing whitespace
    - lower: convert to lowercase
    - upper: convert to uppercase (mutually exclusive with lower)
    """

    df = df.copy()

    if guidance == "on":
        print("🧹 STRING CLEANING STARTED")
        print(f" • Columns: {columns}")

    for col in columns:
        if strip:
            df[col] = df[col].astype(str).str.strip()
            if guidance == "on":
                print(f" → Stripped whitespace: {col}")

        if lower:
            df[col] = df[col].str.lower()
            if guidance == "on":
                print(f" → Lowercased: {col}")

        if upper:
            df[col] = df[col].str.upper()
            if guidance == "on":
                print(f" → Uppercased: {col}")

    if guidance == "on":
        print("✨ String cleaning complete.")

    return df
