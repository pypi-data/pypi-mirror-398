import pandas as pd

def _guide(msg, guidance):
    if guidance == "on":
        print(msg)

def outer_join(df1, df2, on, suffixes=("_left", "_right"), guidance="off"):

    _guide("🔗 Starting FULL OUTER JOIN...", guidance)

    merged = df1.merge(df2, how="outer", on=on, suffixes=suffixes)

    missing_left = merged[merged[on].isna()].shape[0]

    missing_df1 = merged[merged.filter(like="_right").isna().any(axis=1)].shape[0]
    missing_df2 = merged[merged.filter(like="_left").isna().any(axis=1)].shape[0]

    if guidance == "on":
        print(f"⚠️ {missing_df1} df1 rows had no matching df2 key.")
        print(f"⚠️ {missing_df2} df2 rows had no matching df1 key.")
        print("👉 Consider inspecting keys before modelling.")
        print("✨ OUTER JOIN complete.")

    return merged
