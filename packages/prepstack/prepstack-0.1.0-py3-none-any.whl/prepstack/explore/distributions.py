def distribution_report(df, guidance="off"):
    numeric = df.select_dtypes(include="number").describe().T
    categorical = df.select_dtypes(include="object").describe().T

    if guidance == "on":
        print("\n📈 DISTRIBUTION REPORT")
        print("\n🔢 Numeric Columns:")
        print(numeric)
        print("\n🔤 Categorical Columns:")
        print(categorical)

    return {"numeric": numeric, "categorical": categorical}


def distribution_insights(df):
    insights = []
    num_cols = df.select_dtypes(include="number")

    if num_cols.empty:
        return ["No numeric columns detected — skipping distribution insights."]

    skewed = num_cols.skew().abs()
    strong_skew = skewed[skewed > 1]

    if len(strong_skew):
        insights.append(
            f"Highly skewed numeric columns detected: {list(strong_skew.index)} — consider transformation."
        )

    unique_counts = df.nunique()

    high_card = unique_counts[unique_counts > 50]
    if len(high_card):
        insights.append(
            f"High-cardinality categorical columns: {list(high_card.index)} — may affect encoding."
        )

    return insights
