def filter_rows(df, condition, guidance="on"):
    """
    Filter rows using a pandas-query-style expression.

    Example:
        filtered = filter_rows(df, "age > 30 and city == 'Delhi'")
    """
    df2 = df.query(condition)

    if guidance == "on":
        diff = len(df) - len(df2)
        print(f"🔍 Filter applied: '{condition}'")
        print(f"📉 Removed {diff} rows, remaining {len(df2)}")

    return df2
