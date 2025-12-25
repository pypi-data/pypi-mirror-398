import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_timeseries(df, value_col, date_col, guidance="off"):
    apply_theme()

    temp = df.copy()
    temp[date_col] = pd.to_datetime(temp[date_col])
    temp = temp.sort_values(date_col)

    plt.figure(figsize=(10,5))
    plt.plot(temp[date_col], temp[value_col], marker="o", alpha=0.7)

    plt.title(f"Time Series of {value_col}")
    plt.xlabel(date_col)
    plt.ylabel(value_col)
    plt.grid(True)

    if guidance == "on":
        print(f"⏳ Time series plot created for {value_col}")

    plt.show()
