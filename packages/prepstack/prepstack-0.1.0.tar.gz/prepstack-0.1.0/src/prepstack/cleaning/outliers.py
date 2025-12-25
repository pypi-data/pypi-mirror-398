from typing import Optional, Sequence
import pandas as pd
import numpy as np
from prepstack.helpers import say, GuidanceMode


def cap_outliers_iqr(
    df: pd.DataFrame,
    *,
    columns: Optional[Sequence[str]] = None,
    factor: float = 1.5,
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Cap outliers using the IQR method.

    For each numeric column:
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        values below lower are set to lower
        values above upper are set to upper
    """
    df_cap = df.copy()
    num_cols = columns if columns is not None else df_cap.select_dtypes(include="number").columns.tolist()

    if not num_cols:
        say("ℹ️ No numeric columns found for outlier capping.", guidance)
        return df_cap

    say(f"📉 Capping outliers using IQR factor={factor} for columns: {list(num_cols)}", guidance)

    for col in num_cols:
        series = df_cap[col]
        if series.nunique(dropna=True) <= 1:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        before = series.copy()
        df_cap[col] = series.clip(lower, upper)
        changed = (before != df_cap[col]).sum()

        if changed > 0:
            say(f"  • Column '{col}': capped {changed} value(s) outside [{lower:.3f}, {upper:.3f}].", guidance)

    say("✅ Outlier capping complete.", guidance)
    return df_cap
import pandas as pd
from typing import List, Optional

from prepstack.helpers import say, GuidanceMode


def clean_outliers(
    df: pd.DataFrame,
    *,
    columns: Optional[List[str]] = None,
    method: str = "iqr",
    factor: float = 1.5,
    action: str = "remove",  # "remove" | "cap"
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Handle outliers in numeric columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe.
    columns : list[str], optional
        Columns to check. Defaults to all numeric columns.
    method : str
        Outlier detection method. Currently supports:
        - "iqr"
    factor : float
        IQR multiplier (default = 1.5).
    action : str
        How to handle outliers:
        - "remove": drop rows
        - "cap": cap values at bounds
    guidance : "on" | "off"
        Print explanations and warnings.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe.
    """

    df = df.copy()

    if columns is None:
        columns = df.select_dtypes(include="number").columns.tolist()

    if guidance == "on":
        say("🧹 OUTLIER CLEANING STARTED")
        say(f" • Method: {method.upper()}")
        say(f" • Action: {action}")
        say(f" • Columns: {columns}")

    if method != "iqr":
        raise ValueError("Currently only 'iqr' method is supported.")

    mask = pd.Series(False, index=df.index)

    for col in columns:
        if col not in df.columns:
            continue

        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - factor * iqr
        upper = q3 + factor * iqr

        outliers = (df[col] < lower) | (df[col] > upper)

        if guidance == "on":
            say(
                f" → {col}: {outliers.sum()} outliers "
                f"(bounds: {lower:.2f}, {upper:.2f})"
            )

        if action == "remove":
            mask |= outliers

        elif action == "cap":
            df.loc[df[col] < lower, col] = lower
            df.loc[df[col] > upper, col] = upper

        else:
            raise ValueError("action must be 'remove' or 'cap'")

    if action == "remove":
        before = len(df)
        df = df.loc[~mask]
        after = len(df)

        if guidance == "on":
            say(f" 🗑️ Removed {before - after} rows containing outliers")

    if guidance == "on":
        say("✨ Outlier cleaning complete.")

    return df
