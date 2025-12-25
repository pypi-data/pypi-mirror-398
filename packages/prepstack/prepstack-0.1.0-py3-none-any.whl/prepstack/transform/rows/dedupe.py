def drop_duplicates(df, subset=None, keep="first", guidance="on"):
    df = df.copy()
    before = len(df)

    df = df.drop_duplicates(subset=subset, keep=keep)
    after = len(df)

    if guidance == "on":
        print(f"🧹 Removed {before - after} duplicate rows (subset={subset})")

    return df
