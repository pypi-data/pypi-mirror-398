from typing import Literal, Optional, Sequence
import pandas as pd
import numpy as np
from prepstack.helpers import say, GuidanceMode

NumericStrategy = Literal["mean", "median", "zero"]
CatStrategy = Literal["mode", "constant"]


def fill_missing_numeric(
    df: pd.DataFrame,
    *,
    strategy: NumericStrategy = "median",
    columns: Optional[Sequence[str]] = None,
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Fill missing values in numeric columns.

    strategy: 'mean', 'median', or 'zero'
    columns: list of columns to process, or None = all numeric columns
    """
    df_filled = df.copy()
    num_cols = columns if columns is not None else df_filled.select_dtypes(include="number").columns.tolist()

    if not num_cols:
        say("ℹ️ No numeric columns found for missing-value imputation.", guidance)
        return df_filled

    say(f"🔧 Numeric missing-value strategy = '{strategy}' on columns: {list(num_cols)}", guidance)

    for col in num_cols:
        missing_before = df_filled[col].isna().sum()
        if missing_before == 0:
            continue

        if strategy == "mean":
            value = df_filled[col].mean()
        elif strategy == "median":
            value = df_filled[col].median()
        elif strategy == "zero":
            value = 0
        else:
            raise ValueError(f"Unknown strategy '{strategy}' for numeric columns.")

        df_filled[col] = df_filled[col].fillna(value)
        say(f"  • Filled {missing_before} missing value(s) in '{col}' with {strategy}={value:.4f}", guidance)

    say("✅ Numeric missing-value imputation complete.", guidance)
    return df_filled


def fill_missing_categorical(
    df: pd.DataFrame,
    *,
    strategy: CatStrategy = "mode",
    fill_value: Optional[str] = "Unknown",
    columns: Optional[Sequence[str]] = None,
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Fill missing values in categorical/object columns.

    strategy: 'mode' → fill with most frequent value
              'constant' → fill with fill_value (default: 'Unknown')
    """
    df_filled = df.copy()
    cat_cols = columns if columns is not None else df_filled.select_dtypes(include=["object", "category"]).columns.tolist()

    if not cat_cols:
        say("ℹ️ No categorical columns found for missing-value imputation.", guidance)
        return df_filled

    say(f"🔧 Categorical missing-value strategy = '{strategy}' on columns: {list(cat_cols)}", guidance)

    for col in cat_cols:
        missing_before = df_filled[col].isna().sum()
        if missing_before == 0:
            continue

        if strategy == "mode":
            mode_val = df_filled[col].mode(dropna=True)
            value = mode_val.iloc[0] if not mode_val.empty else fill_value
        elif strategy == "constant":
            value = fill_value
        else:
            raise ValueError(f"Unknown strategy '{strategy}' for categorical columns.")

        df_filled[col] = df_filled[col].fillna(value)
        say(f"  • Filled {missing_before} missing value(s) in '{col}' with '{value}'", guidance)

    say("✅ Categorical missing-value imputation complete.", guidance)
    return df_filled


def clean_missing(
    df: pd.DataFrame,
    *,
    numeric_strategy: NumericStrategy = "median",
    cat_strategy: CatStrategy = "mode",
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Convenience helper:
    - fills numeric columns using numeric_strategy
    - fills categorical columns using cat_strategy
    """
    say("🧩 Starting combined missing-value handling.", guidance)
    df2 = fill_missing_numeric(df, strategy=numeric_strategy, guidance=guidance)
    df3 = fill_missing_categorical(df2, strategy=cat_strategy, guidance=guidance)
    say("✨ Combined missing-value cleaning complete.", guidance)
    return df3
