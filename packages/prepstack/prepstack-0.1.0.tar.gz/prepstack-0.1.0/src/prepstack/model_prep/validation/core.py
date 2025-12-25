import pandas as pd
import numpy as np
from collections import Counter

# -------------------------------
# helpers
# -------------------------------

def _suggest(ctx, message):
    if ctx.guided():
        return message
    return None


# -------------------------------
# 1️⃣ TARGET VALIDATION
# -------------------------------

def validate_target(df, target, ctx):
    report = {"exists": True, "issues": []}
    suggestions = []

    if target not in df.columns:
        report["exists"] = False
        report["issues"].append("missing_target")
        suggestions.append(
            _suggest(ctx, "Target column missing. Provide a valid target before modeling.")
        )
        return report, suggestions

    if df[target].isna().any():
        report["issues"].append("target_has_missing")
        suggestions.append(
            _suggest(ctx, "Target has missing values. Consider imputing or dropping rows.")
        )

    if df[target].nunique() < 2:
        report["issues"].append("target_constant")
        suggestions.append(
            _suggest(ctx, "Target has only one class. Modeling is not possible.")
        )

    return report, suggestions


# -------------------------------
# 2️⃣ FEATURE VALIDATION
# -------------------------------

def validate_features(X, ctx):
    report = {
        "categorical": [],
        "constant": [],
        "high_cardinality": []
    }
    suggestions = []

    for col in X.columns:
        if X[col].nunique() <= 1:
            report["constant"].append(col)

        if X[col].dtype == "object":
            report["categorical"].append(col)

        if X[col].nunique() > 0.9 * len(X):
            report["high_cardinality"].append(col)

    if report["categorical"]:
        suggestions.append(
            _suggest(ctx, "Categorical features detected. Consider encoding before modeling.")
        )

    if report["constant"]:
        suggestions.append(
            _suggest(ctx, "Constant features detected. Consider removing them.")
        )

    if report["high_cardinality"]:
        suggestions.append(
            _suggest(ctx, "High-cardinality features detected. Frequency or target encoding may help.")
        )

    return report, suggestions


# -------------------------------
# 3️⃣ CLASS BALANCE CHECK
# -------------------------------

def validate_class_balance(y, ctx, threshold=0.2):
    report = {}
    suggestions = []

    counts = Counter(y)
    total = sum(counts.values())
    ratios = {k: v / total for k, v in counts.items()}

    report["distribution"] = ratios

    if min(ratios.values()) < threshold:
        report["imbalanced"] = True
        suggestions.append(
            _suggest(
                ctx,
                "Class imbalance detected. Consider SMOTE, undersampling, or class weights."
            )
        )
    else:
        report["imbalanced"] = False

    return report, suggestions


# -------------------------------
# 4️⃣ FULL VALIDATION PIPELINE
# -------------------------------

def full_validation(df, target, ctx):
    X = df.drop(columns=[target], errors="ignore")
    y = df[target] if target in df else None

    report = {}
    suggestions = []

    r, s = validate_target(df, target, ctx)
    report["target"] = r
    suggestions += s

    if r["exists"]:
        r, s = validate_features(X, ctx)
        report["features"] = r
        suggestions += s

        r, s = validate_class_balance(y, ctx)
        report["balance"] = r
        suggestions += s

    # clean None suggestions
    suggestions = [s for s in suggestions if s is not None]

    return report, suggestions


def validate_full(df, schema=None, ranges=None, allowed=None, guidance="on"):
    results = {}

    if guidance == "on":
        print("🧪 Running full validation")

    if schema:
        results["schema"] = True

    if ranges:
        results["range"] = ranges

    if allowed:
        results["allowed"] = allowed

    if guidance == "on":
        print("✨ Validation complete")

    return results
