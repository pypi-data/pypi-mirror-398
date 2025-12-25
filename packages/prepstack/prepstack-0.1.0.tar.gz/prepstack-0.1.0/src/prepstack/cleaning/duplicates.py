from typing import Optional, Sequence
import pandas as pd
from prepstack.helpers import say, GuidanceMode

import pandas as pd

def clean_duplicates(df, subset=None, keep="first", guidance="on"):
    """
    Remove duplicate rows from a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
    subset : list or None
        Columns to consider for duplicate detection.
    keep : {"first", "last", False}
        Which duplicates to keep.
    guidance : {"on", "off"}
        Print what is happening.

    Returns
    -------
    pandas.DataFrame
    """

    df = df.copy()
    before = len(df)

    df = df.drop_duplicates(subset=subset, keep=keep)

    after = len(df)

    if guidance == "on":
        removed = before - after
        print(f"🧹 Duplicate cleaning complete")
        print(f" • Rows before: {before}")
        print(f" • Rows after : {after}")
        print(f" • Removed    : {removed}")

    return df



def drop_full_duplicates(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[str]] = None,
    keep: str = "first",
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Drop duplicate rows.

    subset: columns to consider duplicates on (None = all columns)
    keep: 'first', 'last', or False (like pandas)
    """
    df_clean = df.copy()
    before = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=subset, keep=keep)
    removed = before - len(df_clean)

    if removed > 0:
        if subset is None:
            say(f"📉 Removed {removed} fully duplicate row(s).", guidance)
        else:
            say(f"📉 Removed {removed} duplicate row(s) based on columns {list(subset)}.", guidance)
    else:
        say("ℹ️ No duplicate rows found to drop.", guidance)

    return df_clean


def mark_duplicates(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[str]] = None,
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Add a boolean '_is_duplicate' column that marks duplicates.
    """
    df_marked = df.copy()
    df_marked["_is_duplicate"] = df_marked.duplicated(subset=subset, keep="first")
    n_dupes = df_marked["_is_duplicate"].sum()

    if subset is None:
        say(f"🔎 Marked {n_dupes} duplicate row(s) (full row comparison).", guidance)
    else:
        say(f"🔎 Marked {n_dupes} duplicate row(s) based on columns {list(subset)}.", guidance)

    return df_marked


def deduplicate(
    df: pd.DataFrame,
    *,
    subset: Optional[Sequence[str]] = None,
    keep: str = "first",
    guidance: GuidanceMode = "on",
) -> pd.DataFrame:
    """
    Convenience wrapper:
    - marks duplicates
    - drops them
    """
    say("🧬 Starting deduplication (mark + drop).", guidance)
    df_marked = mark_duplicates(df, subset=subset, guidance=guidance)
    df_clean = drop_full_duplicates(df_marked, subset=subset, keep=keep, guidance=guidance)
    say("✨ Deduplication complete.", guidance)
    return df_clean
