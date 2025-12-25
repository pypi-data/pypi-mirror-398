def sort_rows(df, by, ascending=True, guidance="on"):
    df2 = df.sort_values(by=by, ascending=ascending)

    if guidance == "on":
        print(f"🔽 Sorted by {by} (ascending={ascending})")

    return df2
