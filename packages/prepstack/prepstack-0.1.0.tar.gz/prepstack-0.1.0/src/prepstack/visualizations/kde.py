import matplotlib.pyplot as plt
from prepsatck.visualizations.themes import apply_theme
import seaborn as sns

def plot_kde(df, column, guidance="off"):
    apply_theme()

    plt.figure(figsize=(8,5))
    sns.kdeplot(df[column].dropna(), fill=True, alpha=0.7)

    plt.title(f"KDE Plot of {column}")
    plt.xlabel(column)
    plt.grid(True)

    if guidance == "on":
        print(f"🌊 KDE plot generated for {column}")

    plt.show()
