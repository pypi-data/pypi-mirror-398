def build_theme(
    figure_face="#0C0420",
    axes_face="#0A0318",
    text_color="#E6E6E6",
    grid_color="#FFFFFF",
    grid_alpha=0.08,
    title_size=18,
    font="Arial",
    guidance="off"
):
    theme = {
        "figure_face": figure_face,
        "axes_face": axes_face,
        "text_color": text_color,
        "grid_color": grid_color,
        "grid_alpha": grid_alpha,
        "title_size": title_size,
        "font": font
    }

    if guidance == "on":
        print("🎨 Custom theme created:")
        for k, v in theme.items():
            print(f"  • {k} = {v}")

    return theme
