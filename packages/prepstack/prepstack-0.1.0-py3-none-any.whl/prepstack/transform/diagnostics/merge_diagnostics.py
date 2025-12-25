import pandas as pd

def analyse_merge(df1, df2, on, guidance="on"):
    """
    Analyse what will happen BEFORE performing a merge.

    Detects:
    - duplicate keys on both sides
    - one-to-many or many-to-many relationships
    - missing keys on either side
    - potential merge explosion (row multiplication)
    - best recommended join
    """

    if guidance == "on":
        print("🧪 MERGE DIAGNOSTICS REPORT")
        print("────────────────────────────")

    # Duplicate detection
    dup1 = df1[on].duplicated().sum()
    dup2 = df2[on].duplicated().sum()

    if guidance == "on":
        print(f"🔑 Key Column: '{on}'")
        print(f" • Duplicates in df1: {dup1}")
        print(f" • Duplicates in df2: {dup2}")

    # Unique keys
    unique1 = df1[on].nunique()
    unique2 = df2[on].nunique()

    # Missing keys
    missing_in_df2 = unique1 - df1[on].isin(df2[on]).sum()
    missing_in_df1 = unique2 - df2[on].isin(df1[on]).sum()

    if guidance == "on":
        print(f" • Keys in df1 not found in df2: {missing_in_df2}")
        print(f" • Keys in df2 not found in df1: {missing_in_df1}")

    # Relationship type
    if dup1 == 0 and dup2 == 0:
        relation = "1:1"
    elif dup1 > 0 and dup2 == 0:
        relation = "many-to-1"
    elif dup1 == 0 and dup2 > 0:
        relation = "1-to-many"
    else:
        relation = "many-to-many"

    if guidance == "on":
        print(f"🔍 Relationship Type: {relation}")

    # Recommended merge strategy
    if relation == "1:1":
        recommendation = "inner_join"
    elif relation == "many-to-1":
        recommendation = "left_join"
    elif relation == "1-to-many":
        recommendation = "right_join"
    else:
        recommendation = "outer_join"

    if guidance == "on":
        print(f"💡 Recommended Join: {recommendation}")
        print("────────────────────────────")

    return {
        "duplicates_df1": dup1,
        "duplicates_df2": dup2,
        "missing_in_df2": missing_in_df2,
        "missing_in_df1": missing_in_df1,
        "relationship": relation,
        "recommended_join": recommendation
    }
