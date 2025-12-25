import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_category_ratio(df, column, guidance="off"):
    apply_theme()

    ratio = df[column].value_counts(normalize=True) * 100

    plt.figure(figsize=(8,5))
    ratio.plot(kind="bar")

    plt.title(f"Category Ratio (%) - {column}")
    plt.xlabel(column)
    plt.ylabel("Percentage")
    plt.grid(True)

    if guidance == "on":
        print(f"📊 Category ratio plotted for: {column}")

    plt.show()
