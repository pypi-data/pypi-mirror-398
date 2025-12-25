import pandas as pd

def reset_index_smart(df, guidance="on"):
    df = df.copy()

    # Check if index is already clean
    if df.index.is_monotonic_increasing and df.index.equals(pd.RangeIndex(len(df))):
        if guidance == "on":
            print("✨ Index already clean — no reset needed.")
        return df

    # Reset index
    df = df.reset_index(drop=True)

    if guidance == "on":
        print("🔄 Index reset performed.")

    return df
