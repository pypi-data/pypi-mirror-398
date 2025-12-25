import numpy as np
import pandas as pd

# ----------------------------
# 1. Correlation-based selector
# ----------------------------
def corr_selector(
    df,
    target=None,
    threshold=0.9,
    method="pearson",
    guidance="on"
):
    """
    Remove highly correlated features.

    Parameters
    ----------
    df : pd.DataFrame
    target : str or None
        Target column name (will be excluded from correlation)
    threshold : float
        Correlation cutoff
    """

    df = df.copy()

    if target is not None:
        X = df.drop(columns=[target])
    else:
        X = df

    numeric = X.select_dtypes(include="number")

    if numeric.shape[1] < 2:
        if guidance == "on":
            print("⚠️ Not enough numeric features for correlation check.")
        return numeric.columns.tolist()

    corr = numeric.corr(method=method).abs()

    upper = corr.where(
        np.triu(np.ones(corr.shape), k=1).astype(bool)
    )

    to_drop = [
        col for col in upper.columns
        if any(upper[col] > threshold)
    ]

    if guidance == "on":
        print(f"🔗 Computing {method} correlations for {numeric.shape[1]} features...")
        for col in to_drop:
            culprit = upper[col][upper[col] > threshold].idxmax()
            print(f" • Removing '{col}' (corr with '{culprit}' = {upper[col].max():.2f})")

        print(
            f"✅ Correlation selector finished. "
            f"Kept {numeric.shape[1] - len(to_drop)} features "
            f"({len(to_drop)} removed)."
        )

    return [c for c in numeric.columns if c not in to_drop]


# ----------------------------
# 2. Variance selector
# ----------------------------
def variance_selector(df, threshold=0.0, guidance="on"):
    """
    Remove low-variance features.
    Returns list of kept feature names.
    """

    from sklearn.feature_selection import VarianceThreshold

    selector = VarianceThreshold(threshold=threshold)
    selector.fit(df)

    kept = df.columns[selector.get_support()].tolist()
    removed = [c for c in df.columns if c not in kept]

    if guidance == "on":
        print(f"📏 Variance thresholding: removing features with variance <= {threshold}")
        if removed:
            print(f" → Removed {len(removed)} constant/near-constant features: {removed}")
        else:
            print(" → No features removed.")

    return kept


# ----------------------------
# 3. Mutual Information selector
# ----------------------------
def mutual_info_selector(
    X,
    y,
    k=None,
    threshold=0.0,
    guidance="on"
):
    """
    Mutual Information feature selection.

    Parameters
    ----------
    X : pd.DataFrame
    y : pd.Series
    k : int or None
        Number of top features to keep.
        If None, keep all with MI > threshold.
    threshold : float
        Minimum MI score (used only if k=None)
    """

    from sklearn.feature_selection import mutual_info_classif

    X = X.copy()

    mi = mutual_info_classif(X, y, random_state=42)
    mi_scores = pd.Series(mi, index=X.columns)

    if k is not None:
        selected = mi_scores.sort_values(ascending=False).head(k)
    else:
        selected = mi_scores[mi_scores > threshold]

    if guidance == "on":
        print("🧠 Mutual information feature selection started")
        print(f" → Selected {len(selected)} features with MI > {threshold}")
        for f, v in selected.items():
            print(f"   • {f}: {v:.4f}")

    return selected.index.tolist()



# ----------------------------
# 4. Model-based selector
# ----------------------------
def model_based_selector(
    X,
    y,
    k=10,
    model="auto",
    guidance="on"
):
    """
    Model-based feature selection using feature importance.

    Parameters
    ----------
    X : pd.DataFrame
    y : pd.Series
    k : int
        Number of top features to keep
    model : "auto" | "xgb" | "rf"
    """

    X = X.copy()

    # --- choose model ---
    if model in ("auto", "xgb"):
        try:
            from xgboost import XGBClassifier
            clf = XGBClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                eval_metric="logloss",
                random_state=42
            )
            used_model = "XGBoost"
        except ImportError:
            model = "rf"

    if model == "rf":
        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=-1
        )
        used_model = "RandomForest"

    # --- fit ---
    clf.fit(X, y)

    # --- importance ---
    importances = pd.Series(
        clf.feature_importances_,
        index=X.columns
    ).sort_values(ascending=False)

    selected = importances.head(k)

    if guidance == "on":
        print(f"🌲 Model-based feature selection using {used_model}")
        print(f" → Selected top-{k} features")
        for f, v in selected.items():
            print(f"   • {f}: {v:.4f}")

    return selected.index.tolist(), selected

# ----------------------------
# 5. Combined pipeline
# ----------------------------
def combined_feature_selection(df, target, guidance="on"):

    if guidance == "on":
        print("🔁 Starting combined feature selection pipeline")

    X = df.drop(columns=[target])
    y = df[target]

    # 1️⃣ Variance
    kept_var = variance_selector(X, guidance=guidance)
    X1 = X[kept_var]

    # 2️⃣ Correlation
    kept_corr = corr_selector(X1, guidance=guidance)
    X2 = X1[kept_corr]

    # 3️⃣ Mutual Info
    kept_mi = mutual_info_selector(X2, y, guidance=guidance)
    X3 = X2[kept_mi]

    # 4️⃣ Model-based
    kept_model, _ = model_based_selector(
        X3, y, k=min(5, X3.shape[1]), guidance=guidance
    )

    if guidance == "on":
        print(f"🎯 Combined selection finished. Final {len(kept_model)} features selected.")

    return kept_model
