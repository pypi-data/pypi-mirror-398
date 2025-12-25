import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_rolling(df, value_col, date_col, window=7, guidance="off"):
    apply_theme()

    temp = df.copy()
    temp[date_col] = pd.to_datetime(temp[date_col])
    temp = temp.sort_values(date_col)

    temp["rolling"] = temp[value_col].rolling(window).mean()

    plt.figure(figsize=(10,5))
    plt.plot(temp[date_col], temp["rolling"], linewidth=2)

    plt.title(f"{window}-Day Rolling Average: {value_col}")
    plt.xlabel(date_col)
    plt.ylabel(value_col)
    plt.grid(True)

    if guidance == "on":
        print(f"📉 Rolling average ({window} days) plotted for {value_col}")

    plt.show()
