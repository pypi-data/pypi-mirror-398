import pandas as pd

def _guide(msg, guidance):
    if guidance == "on":
        print(msg)

def inner_join(df1, df2, on, suffixes=("_left", "_right"), guidance="off"):

    _guide("🔗 Starting INNER JOIN...", guidance)

    before1 = len(df1)
    before2 = len(df2)

    merged = df1.merge(df2, how="inner", on=on, suffixes=suffixes)

    after = len(merged)

    # dropped rows detection
    dropped_df1 = before1 - merged[on].nunique()
    dropped_df2 = before2 - merged[on].nunique()

    if dropped_df1 > 0:
        _guide(f"⚠️ {dropped_df1} rows from df1 did NOT match df2.", guidance)

    if dropped_df2 > 0:
        _guide(f"⚠️ {dropped_df2} rows from df2 did NOT match df1.", guidance)

    _guide("✨ INNER JOIN complete.", guidance)
    return merged
