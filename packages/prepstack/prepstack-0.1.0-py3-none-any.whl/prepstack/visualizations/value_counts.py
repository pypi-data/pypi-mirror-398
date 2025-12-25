import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_value_counts(df, column, guidance="off"):
    apply_theme()

    counts = df[column].value_counts()

    plt.figure(figsize=(8,5))
    counts.plot(kind="bar")

    plt.title(f"Value Counts of {column}")
    plt.xlabel(column)
    plt.ylabel("Count")
    plt.grid(True)

    if guidance == "on":
        print(f"🔢 Value counts plotted for {column}")

    plt.show()
