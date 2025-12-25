import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_histogram(df, column, bins=30, guidance="off"):
    apply_theme()

    plt.figure(figsize=(8,5))
    plt.hist(df[column].dropna(), bins=bins, alpha=0.8)

    plt.title(f"Histogram of {column}")
    plt.xlabel(column)
    plt.ylabel("Frequency")
    plt.grid(True)

    if guidance == "on":
        print(f"📊 Histogram plotted for column: {column}")

    plt.show()
