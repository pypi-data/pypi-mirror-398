import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# =====================================================
# 1. APPLY DEFAULT prepstack THEME
# =====================================================
def apply_theme():

    # Backgrounds
    plt.rcParams["figure.facecolor"] = "#0C0420"
    plt.rcParams["axes.facecolor"]  = "#0A0318"
    plt.rcParams["savefig.facecolor"] = "#0C0420"

    # Text colors
    plt.rcParams["text.color"] = "#E6E6E6"
    plt.rcParams["axes.labelcolor"] = "#E6E6E6"
    plt.rcParams["xtick.color"] = "#E6E6E6"
    plt.rcParams["ytick.color"] = "#E6E6E6"

    # Titles
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.titlesize"] = 18

    # Grid lines
    plt.rcParams["grid.color"] = "#FFFFFF"
    plt.rcParams["grid.alpha"] = 0.08
    plt.rcParams["grid.linestyle"] = "--"

    # Border + patch aesthetics
    plt.rcParams["axes.edgecolor"] = "#E6E6E6"
    plt.rcParams["patch.edgecolor"] = "#0C0420"

    # DEFAULT FONT — ARIAL (always available)
    plt.rcParams["font.family"] = "Arial"


# =====================================================
# 2. LOAD CUSTOM FONTS (ONLY WHEN USER PROVIDES THEM)
# =====================================================
def load_custom_fonts(font_paths, guidance="off"):

    for path in font_paths:
        if os.path.exists(path):
            fm.fontManager.addfont(path)

            if guidance == "on":
                print(f"✨ Loaded custom font: {path}")

        else:
            if guidance == "on":
                print(f"⚠️ Font not found (skipped): {path}")
