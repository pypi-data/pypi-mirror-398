import pandas as pd

def _guide(msg, guidance):
    if guidance == "on":
        print(msg)

def right_join(df1, df2, on, suffixes=("_left", "_right"), guidance="off"):

    _guide("🔗 Starting RIGHT JOIN...", guidance)

    if df1[on].duplicated().any():
        _guide(f"⚠️ df1 has duplicate keys → row expansion possible.", guidance)

    if df2[on].duplicated().any():
        _guide(f"⚠️ df2 has duplicate keys → row expansion likely.", guidance)

    before = len(df2)

    merged = df1.merge(df2, how="right", on=on, suffixes=suffixes)

    after = len(merged)

    missing_matches = merged[on].isna().sum()
    if missing_matches > 0:
        _guide(f"⚠️ {missing_matches} rows from df2 had no match in df1.", guidance)

    if after > before:
        _guide(f"⚠️ Row expansion detected: {before} → {after}", guidance)

    _guide("✨ RIGHT JOIN complete.", guidance)
    return merged
