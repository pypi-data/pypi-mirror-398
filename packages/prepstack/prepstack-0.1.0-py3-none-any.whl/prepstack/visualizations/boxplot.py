import matplotlib.pyplot as plt
from prepstack.visualizations.themes import apply_theme

def plot_box(df, column, guidance="off"):
    apply_theme()

    plt.figure(figsize=(6,5))
    plt.boxplot(df[column].dropna(), vert=True)

    plt.title(f"Boxplot of {column}")
    plt.ylabel(column)
    plt.grid(True)

    if guidance == "on":
        print(f"📦 Boxplot generated for {column}")

    plt.show()
