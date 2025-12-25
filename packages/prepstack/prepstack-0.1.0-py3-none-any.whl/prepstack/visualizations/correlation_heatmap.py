import matplotlib.pyplot as plt
import seaborn as sns
from prepstack.visualizations.themes import apply_theme

def plot_correlation_heatmap(df, guidance="off"):
    apply_theme()

    numeric_df = df.select_dtypes(include="number")
    corr = numeric_df.corr()

    plt.figure(figsize=(10,8))
    sns.heatmap(corr, annot=False, cmap="rocket", linewidths=0.5)

    plt.title("Correlation Heatmap")
    plt.grid(False)

    if guidance == "on":
        print("🔗 Correlation heatmap generated.")

    plt.show()
