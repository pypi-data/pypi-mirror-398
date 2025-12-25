from typing import Optional
import pandas as pd
from prepstack.helpers import say, GuidanceMode


def clean_basic(
    df: pd.DataFrame,
    *,
    drop_constant: bool = True,
    drop_duplicates: bool = True,
    reset_index: bool = True,
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Basic structural cleaning:
    - strip whitespace from column names
    - (optional) drop constant columns
    - (optional) drop duplicate rows
    - (optional) reset index

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    drop_constant : bool, default True
        If True, drop columns with only one unique non-null value.
    drop_duplicates : bool, default True
        If True, drop duplicate rows.
    reset_index : bool, default True
        If True, reset index after cleaning.
    guidance : {'on', 'off'}, default 'on'
        Controls printed explanations.
    """
    df_clean = df.copy()

    # 1) Strip whitespace in column names
    original_cols = list(df_clean.columns)
    df_clean.columns = [c.strip() if isinstance(c, str) else c for c in df_clean.columns]
    n_stripped = sum(
        1 for old, new in zip(original_cols, df_clean.columns)
        if isinstance(old, str) and old != new
    )

    if n_stripped > 0:
        say(f"🧹 Stripped whitespace from {n_stripped} column name(s).", guidance)

    # 2) Drop constant columns
    dropped_constants = []
    if drop_constant:
        for col in df_clean.columns:
            nunique = df_clean[col].nunique(dropna=True)
            if nunique <= 1:
                dropped_constants.append(col)

        if dropped_constants:
            df_clean = df_clean.drop(columns=dropped_constants)
            say(f"🚮 Dropped {len(dropped_constants)} constant column(s): {dropped_constants}", guidance)

    # 3) Drop duplicate rows
    removed_dupes = 0
    if drop_duplicates:
        before = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed_dupes = before - len(df_clean)
        if removed_dupes > 0:
            say(f"📉 Removed {removed_dupes} duplicate row(s).", guidance)

    # 4) Reset index
    if reset_index:
        df_clean = df_clean.reset_index(drop=True)
        say("✨ Index reset.", guidance)

    say("✨ Basic cleaning complete.", guidance)
    return df_clean
