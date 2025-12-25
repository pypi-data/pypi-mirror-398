def clean_types(df, schema=None, guidance="on"):
    """
    Standardize column data types.

    Parameters
    ----------
    df : pandas.DataFrame
    schema : dict, optional
        Example: {"age": "int64", "price": "float64", "date": "datetime64[ns]"}
    guidance : "on" | "off"
    """

    import pandas as pd

    df = df.copy()

    if schema is None:
        if guidance == "on":
            print("ℹ️ No schema provided — skipping type casting")
        return df

    if guidance == "on":
        print("🔧 TYPE CASTING STARTED")

    for col, dtype in schema.items():
        if col not in df.columns:
            if guidance == "on":
                print(f" ⚠️ Column '{col}' not found — skipped")
            continue

        try:
            if "datetime" in dtype:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                df[col] = df[col].astype(dtype)

            if guidance == "on":
                print(f" ✔ Cast '{col}' → {dtype}")

        except Exception as e:
            if guidance == "on":
                print(f" ❌ Failed casting '{col}' → {dtype}: {e}")

    if guidance == "on":
        print("✨ Type casting complete.")

    return df
