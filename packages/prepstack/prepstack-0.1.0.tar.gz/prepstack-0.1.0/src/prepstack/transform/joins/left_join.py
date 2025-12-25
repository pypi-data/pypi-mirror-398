import pandas as pd

def _guide(msg, guidance):
    if guidance == "on":
        print(msg)

def left_join(df1, df2, on, suffixes=("_left", "_right"), guidance="off"):

    _guide("🔗 Starting LEFT JOIN...", guidance)

    # duplicate key detection
    if df1[on].duplicated().any():
        _guide(f"⚠️ df1 has duplicate keys in '{on}'. This may create row multiplication.", guidance)

    if df2[on].duplicated().any():
        _guide(f"⚠️ df2 has duplicate keys in '{on}'. LEFT join will create expanded rows.", guidance)

    before = len(df1)

    merged = df1.merge(df2, how="left", on=on, suffixes=suffixes)

    after = len(merged)

    # missing detection (right table didn't match)
    missing_matches = merged[on].isna().sum()
    if missing_matches > 0:
        _guide(f"⚠️ {missing_matches} rows could not find a match in df2.", guidance)
        _guide("👉 Suggested next step: prepstack.cleaning.fill_missing()", guidance)

    # merge explosion detection
    if after > before:
        _guide(f"⚠️ Row count expanded from {before} → {after}. Check duplicates in merge key.", guidance)

    _guide("✨ LEFT JOIN complete.", guidance)
    return merged
