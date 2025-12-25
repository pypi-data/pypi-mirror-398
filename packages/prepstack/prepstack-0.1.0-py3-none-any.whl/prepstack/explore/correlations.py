def correlation_report(df, guidance="off"):
    numeric = df.select_dtypes(include="number")

    if numeric.shape[1] < 2:
        if guidance == "on":
            print("⚠️ Not enough numeric columns for correlation.")
        return None

    corr = numeric.corr()

    if guidance == "on":
        print("\n🔗 CORRELATION MATRIX")
        print(corr)

        strong = (corr.abs() > 0.5) & (corr.abs() < 1)
        strong_pairs = strong[strong].stack()

        if len(strong_pairs):
            print("\n🔥 Strong correlations found:")
            print(strong_pairs)

    return corr


def correlation_insights(corr):
    insights = []
    if corr is None:
        return ["Correlation could not be computed."]

    strong = corr[(corr.abs() > 0.5) & (corr.abs() < 1)]

    if (strong.abs().sum().sum() == 0):
        insights.append("No strong correlations detected.")
    else:
        insights.append("Strong linear relationships detected — consider multicollinearity management.")

    return insights
