import pandas as pd

def dataset_overview(df, guidance="off"):
    overview = {
        "rows": len(df),
        "columns": df.shape[1],
        "column_names": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "memory_MB": round(df.memory_usage(deep=True).sum() / 1_000_000, 3)
    }

    if guidance == "on":
        print("📊 DATASET OVERVIEW")
        print(f"• Rows: {overview['rows']}")
        print(f"• Columns: {overview['columns']}")
        print(f"• Memory usage: {overview['memory_MB']} MB")
        print("")

    return overview


def overview_insights(df):
    insights = []
    rows, cols = df.shape

    if rows < 500:
        insights.append("Dataset is small and easy to process.")
    elif rows < 50_000:
        insights.append("Dataset is moderately sized; normal ML workflows apply.")
    else:
        insights.append("Large dataset detected — consider chunking or Dask.")

    nulls = df.isna().sum().sum()
    if nulls == 0:
        insights.append("No missing values — excellent data quality.")
    else:
        insights.append(f"Dataset contains {nulls} missing values — requires cleaning.")

    object_cols = df.select_dtypes(include="object").columns
    if len(object_cols) > cols * 0.3:
        insights.append("High number of categorical columns — consider encoding strategies.")

    num_cols = df.select_dtypes(include="number").columns
    if len(num_cols) > cols * 0.7:
        insights.append("Dataset is numerically heavy — scaling may be needed.")

    return insights
