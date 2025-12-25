import pandas as pd

def _print(guidance, *msgs):
    if guidance == "on":
        print(*msgs)

# -------------------------
# One-hot encoding
# -------------------------
def one_hot_encode(df, columns, drop_first=True, prefix_sep="_", guidance="off"):
    """
    One-hot encode specified categorical columns.
    Returns a new DataFrame.
    """
    df = df.copy()
    _print(guidance, f"🧩 ONE-HOT ENCODING STARTED • columns={columns} drop_first={drop_first}")
    for col in columns:
        if col not in df.columns:
            _print(guidance, f"⚠️ Column '{col}' not found — skipping.")
            continue
        dummies = pd.get_dummies(df[col], prefix=col, drop_first=drop_first)
        df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
        _print(guidance, f" → Encoded '{col}' with {dummies.shape[1]} columns")
    _print(guidance, "✨ One-hot encoding complete.")
    return df

# -------------------------
# Label encoding (simple)
# -------------------------
def label_encode(df, columns, mapping=None, guidance="off"):
    """
    Label encode columns. If mapping provided (dict col -> dict), use that mapping.
    Otherwise create mapping automatically.
    Returns (df, mappings)
    """
    df = df.copy()
    mappings = {}
    _print(guidance, f"🔢 LABEL ENCODING STARTED • columns={columns}")
    for col in columns:
        if col not in df.columns:
            _print(guidance, f"⚠️ Column '{col}' not found — skipping.")
            continue
        if mapping and col in mapping:
            mp = mapping[col]
        else:
            cats = pd.Series(df[col].astype("category").cat.categories)
            mp = {k: i for i, k in enumerate(cats)}
        df[col] = df[col].map(mp).fillna(-1).astype(int)
        mappings[col] = mp
        _print(guidance, f" → Created mapping for '{col}': {list(mp.items())[:6]}{'...' if len(mp)>6 else ''}")
    _print(guidance, "✨ Label encoding complete.")
    return df, mappings

# -------------------------
# Frequency encoding
# -------------------------
def frequency_encode(df, columns, guidance="off"):
    """
    Replace categories with their frequency (proportion) in each column.
    """
    df = df.copy()
    _print(guidance, f"📊 FREQUENCY ENCODING STARTED • columns={columns}")
    for col in columns:
        if col not in df.columns:
            _print(guidance, f"⚠️ Column '{col}' not found — skipping.")
            continue
        freq = df[col].value_counts(normalize=True)
        df[col + "_freq"] = df[col].map(freq).fillna(0.0)
        _print(guidance, f" → Added '{col}_freq' (unique={freq.shape[0]})")
    _print(guidance, "✨ Frequency encoding complete.")
    return df

import pandas as pd

def encode_category(
    df,
    columns,
    method="onehot",
    drop_first=False,
    guidance="on"
):
    """
    Encode categorical columns.

    Methods:
    - onehot
    - label
    - frequency
    """

    df = df.copy()
    mappings = {}

    if guidance == "on":
        print("🧩 CATEGORY ENCODING STARTED")
        print(f" • Columns: {columns}")
        print(f" • Method: {method}")

    for col in columns:
        if method == "onehot":
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=drop_first)
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)

            if guidance == "on":
                print(f" → One-hot encoded '{col}'")

        elif method == "label":
            codes, uniques = pd.factorize(df[col])
            df[col] = codes
            mappings[col] = dict(enumerate(uniques))

            if guidance == "on":
                print(f" → Label encoded '{col}'")

        elif method == "frequency":
            freq = df[col].value_counts(normalize=True)
            df[col + "_freq"] = df[col].map(freq)

            if guidance == "on":
                print(f" → Frequency encoded '{col}'")

        else:
            raise ValueError(f"Unknown encoding method: {method}")

    if guidance == "on":
        print("✨ Encoding complete.")

    return df, mappings if mappings else df
