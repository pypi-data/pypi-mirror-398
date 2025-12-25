import pandas as pd

def missing_report(df, guidance="off"):
    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100

    report = pd.DataFrame({
        "missing_count": missing,
        "missing_percent": missing_percent,
        "dtype": df.dtypes
    })

    report = report[report["missing_count"] > 0]

    if guidance == "on":
        print("\n🧩 MISSING VALUE REPORT")
        if report.empty:
            print("No missing values found. 🎉")
        else:
            print(report)

    return report


def missing_insights(missing_df):
    insights = []
    if missing_df.empty:
        insights.append("Dataset has no missing values — no imputation required.")
        return insights

    high_missing = missing_df[missing_df["missing_percent"] > 40]
    if len(high_missing):
        insights.append("Some columns have >40% missing values — consider dropping them.")

    moderate_missing = missing_df[
        (missing_df["missing_percent"] > 5) &
        (missing_df["missing_percent"] <= 40)
    ]
    if len(moderate_missing):
        insights.append("Columns with 5–40% missing values may need imputation.")

    low_missing = missing_df[missing_df["missing_percent"] <= 5]
    if len(low_missing):
        insights.append("Light missingness — simple imputation will work.")

    return insights
