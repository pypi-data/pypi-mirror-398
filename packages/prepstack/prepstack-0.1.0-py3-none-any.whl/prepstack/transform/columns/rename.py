import re

def rename_columns(df, mapping=None, prefix=None, suffix=None, style=None, guidance="on"):
    """
    Flexible column renamer.
    """
    df = df.copy()

    old_cols = df.columns.tolist()

    if mapping:
        df.rename(columns=mapping, inplace=True)
        if guidance == "on":
            print(f"🔤 Renamed columns using mapping: {mapping}")

    if prefix:
        df.columns = [prefix + c for c in df.columns]
        if guidance == "on":
            print(f"➕ Added prefix '{prefix}'")

    if suffix:
        df.columns = [c + suffix for c in df.columns]
        if guidance == "on":
            print(f"➕ Added suffix '{suffix}'")

    # Style cleaning
    if style == "snake_case":
        df.columns = [re.sub(r'\W+', '_', c).lower() for c in df.columns]
        if guidance == "on":
            print("🐍 Converted to snake_case")

    if style == "lower":
        df.columns = [c.lower() for c in df.columns]

    if style == "upper":
        df.columns = [c.upper() for c in df.columns]

    if guidance == "on":
        print("✨ Renaming complete.")
        print("Old:", old_cols)
        print("New:", df.columns.tolist())

    return df
