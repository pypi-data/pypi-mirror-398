import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedShuffleSplit, GroupShuffleSplit
from sklearn.model_selection import TimeSeriesSplit

# ============================
# 1. SIMPLE SPLIT
# ============================
def simple_split(df, target, test_size=0.2, random_state=42, guidance="on"):
    if guidance == "on":
        print(f"🔀 SIMPLE SPLIT: test_size={test_size}")

    X = df.drop(columns=[target])
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    if guidance == "on":
        print(f" → Train: {len(X_train)} rows")
        print(f" → Test: {len(X_test)} rows")
        print("✨ Simple split complete.")

    return X_train, X_test, y_train, y_test


# ============================
# 2. STRATIFIED SPLIT
# ============================
def stratified_split(df, target, test_size=0.2, random_state=42, guidance="on"):
    if guidance == "on":
        print("🎯 STRATIFIED SPLIT (preserves target distribution)")

    X = df.drop(columns=[target])
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    if guidance == "on":
        print(" → Stratification applied.")
        print(f" → Train: {len(X_train)}, Test: {len(X_test)}")

    return X_train, X_test, y_train, y_test


# ============================
# 3. TIME-BASED SPLIT
# ============================
def time_split(df, date_col, test_size=0.2, guidance="on"):
    df = df.sort_values(date_col)
    split_idx = int(len(df) * (1 - test_size))

    if guidance == "on":
        print(f"⏳ TIME SERIES SPLIT on '{date_col}'")
        print(f" → Train until index {split_idx}")
        print(f" → Test from index {split_idx}")

    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]

    return train, test


# ============================
# 4. GROUP SPLIT
# ============================
def group_split(df, group_col, test_size=0.2, random_state=42, guidance="on"):
    if guidance == "on":
        print(f"👥 GROUP SPLIT by '{group_col}' — ensuring no leakage")

    splitter = GroupShuffleSplit(
        test_size=test_size,
        random_state=random_state
    )

    groups = df[group_col]

    train_idx, test_idx = next(splitter.split(df, groups=groups))

    train = df.iloc[train_idx]
    test = df.iloc[test_idx]

    if guidance == "on":
        print(f" → Train groups: {train[group_col].nunique()}")
        print(f" → Test groups: {test[group_col].nunique()}")

    return train, test


# ============================
# 5. HOLDOUT SPLIT (manual)
# ============================
def holdout_split(df, holdout_ratio=0.1, guidance="on"):
    cutoff = int(len(df) * (1 - holdout_ratio))

    if guidance == "on":
        print(f"📦 HOLDOUT SPLIT (holdout={holdout_ratio})")
        print(f" → Train rows: {cutoff}")
        print(f" → Holdout rows: {len(df) - cutoff}")

    train = df.iloc[:cutoff]
    holdout = df.iloc[cutoff:]

    return train, holdout
