from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

def fit_model(X, y, model_type="logistic", guidance="on"):
    if model_type == "logistic":
        model = LogisticRegression(max_iter=1000)
    elif model_type == "rf":
        model = RandomForestClassifier(n_estimators=100, random_state=42)
    else:
        raise ValueError("Unsupported model_type")

    model.fit(X, y)

    if guidance == "on":
        print(f"🤖 Model trained: {model_type}")

    return model


def predict(model, X):
    return model.predict(X)
