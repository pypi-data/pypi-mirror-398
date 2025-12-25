import pandas as pd
from sklearn.utils import resample

def random_undersample(df, target, guidance="on"):
    """
    Randomly undersample majority class to match minority.
    """

    df = df.copy()

    majority = df[df[target] == df[target].value_counts().idxmax()]
    minority = df[df[target] == df[target].value_counts().idxmin()]

    majority_downsampled = resample(
        majority,
        replace=False,
        n_samples=len(minority),
        random_state=42
    )

    balanced = pd.concat([majority_downsampled, minority])

    if guidance == "on":
        print("⚖️ RANDOM UNDERSAMPLING")
        print(f" → Before: {df[target].value_counts().to_dict()}")
        print(f" → After: {balanced[target].value_counts().to_dict()}")

    return balanced.sample(frac=1, random_state=42)

def random_oversample(df, target, guidance="on"):
    """
    Randomly oversample minority class.
    """

    df = df.copy()

    majority = df[df[target] == df[target].value_counts().idxmax()]
    minority = df[df[target] == df[target].value_counts().idxmin()]

    minority_upsampled = resample(
        minority,
        replace=True,
        n_samples=len(majority),
        random_state=42
    )

    balanced = pd.concat([majority, minority_upsampled])

    if guidance == "on":
        print("⚖️ RANDOM OVERSAMPLING")
        print(f" → Before: {df[target].value_counts().to_dict()}")
        print(f" → After: {balanced[target].value_counts().to_dict()}")

    return balanced.sample(frac=1, random_state=42)

from collections import Counter

def smote_balance(X, y, k_neighbors=5, guidance="on"):
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        raise ImportError("imblearn not installed. Install with pip install imbalanced-learn")

    class_counts = Counter(y)
    minority_count = min(class_counts.values())

    if minority_count <= 1:
        raise ValueError("SMOTE cannot be applied: minority class has <=1 samples")

    # auto-adjust k
    k = min(k_neighbors, minority_count - 1)

    if guidance == "on":
        print("🧬 SMOTE BALANCING")
        print(f" • Class distribution before: {dict(class_counts)}")
        print(f" • Using k_neighbors={k}")

    sm = SMOTE(random_state=42, k_neighbors=k)
    X_res, y_res = sm.fit_resample(X, y)

    if guidance == "on":
        print(f" • Class distribution after: {dict(Counter(y_res))}")
        print("✨ SMOTE balancing complete.")

    return X_res, y_res
