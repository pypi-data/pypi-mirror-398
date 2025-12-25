import pandas as pd
import numpy as np

def _print(guidance, *msgs):
    if guidance == "on":
        print(*msgs)

# -------------------------
# Ratio feature
# -------------------------
def add_ratio(df, numerator, denominator, new_name=None, fill_na=None, guidance="off"):
    """
    Add ratio feature numerator / denominator; optional fill_na (numeric)
    """
    df = df.copy()
    new_name = new_name or f"{numerator}_over_{denominator}"
    _print(guidance, f"➗ Creating ratio feature '{new_name}' = {numerator}/{denominator}")
    with np.errstate(divide='ignore', invalid='ignore'):
        df[new_name] = df[numerator] / df[denominator]
    if fill_na is not None:
        df[new_name] = df[new_name].fillna(fill_na)
        _print(guidance, f" → Filled NA in '{new_name}' with {fill_na}")
    return df

# -------------------------
# Interaction feature (product)
# -------------------------
def add_interaction(df, cols, new_name=None, func=None, guidance="off"):
    """
    Create interaction feature from cols list.
    default func = product; can pass any function that accepts DataFrame and returns Series.
    """
    df = df.copy()
    if func is None:
        def prod(df_local):
            out = df_local[cols[0]].astype(float)
            for c in cols[1:]:
                out = out * df_local[c].astype(float)
            return out
        func = prod
    new_name = new_name or "_x_".join(cols)
    _print(guidance, f"✖ Creating interaction '{new_name}' from {cols}")
    df[new_name] = func(df)
    return df

# -------------------------
# Rolling aggregate (time-series style)
# -------------------------
def rolling_aggregate(df, groupby_cols, target_col, window=3, agg="mean", sort_by=None, new_name=None, guidance="off"):
    """
    Compute rolling aggregate within groups.
    - groupby_cols: list
    - target_col: column to aggregate
    - window: int (periods)
    - agg: 'mean'|'sum'|'median'|'max'|'min'
    - sort_by: optional column to sort within groups (e.g. date)
    """
    df = df.copy()
    if sort_by:
        df = df.sort_values(sort_by)
    new_name = new_name or f"{target_col}_rolling_{window}_{agg}"
    _print(guidance, f"🔁 Rolling aggregate on '{target_col}' grouped by {groupby_cols}, window={window}, agg={agg}")
    grouped = df.groupby(groupby_cols)[target_col]
    if agg == "mean":
        df[new_name] = grouped.transform(lambda x: x.rolling(window, min_periods=1).mean())
    elif agg == "sum":
        df[new_name] = grouped.transform(lambda x: x.rolling(window, min_periods=1).sum())
    elif agg == "median":
        df[new_name] = grouped.transform(lambda x: x.rolling(window, min_periods=1).median())
    elif agg == "max":
        df[new_name] = grouped.transform(lambda x: x.rolling(window, min_periods=1).max())
    elif agg == "min":
        df[new_name] = grouped.transform(lambda x: x.rolling(window, min_periods=1).min())
    else:
        raise ValueError("Unknown agg")
    return df

# -------------------------
# Group aggregate features (agg + merge)
# -------------------------
def group_aggregate(df, groupby_cols, target_col, agg="mean", new_name=None, guidance="off"):
    """
    Create group-level aggregate and merge back to original df.
    """
    df = df.copy()
    new_name = new_name or f"{target_col}_group_{agg}"
    _print(guidance, f"📐 Group aggregate '{new_name}' grouping by {groupby_cols} using {agg}")
    if agg == "mean":
        agg_df = df.groupby(groupby_cols)[target_col].mean().reset_index().rename(columns={target_col: new_name})
    elif agg == "sum":
        agg_df = df.groupby(groupby_cols)[target_col].sum().reset_index().rename(columns={target_col: new_name})
    elif agg == "median":
        agg_df = df.groupby(groupby_cols)[target_col].median().reset_index().rename(columns={target_col: new_name})
    elif agg == "count":
        agg_df = df.groupby(groupby_cols)[target_col].count().reset_index().rename(columns={target_col: new_name})
    else:
        raise ValueError("Unknown agg")
    df = df.merge(agg_df, on=groupby_cols, how="left")
    return df
