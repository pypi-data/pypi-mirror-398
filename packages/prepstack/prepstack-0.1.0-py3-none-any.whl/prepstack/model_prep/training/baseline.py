from sklearn.dummy import DummyClassifier, DummyRegressor

def baseline_model(y, task="classification", guidance="on"):
    if guidance == "on":
        print("📊 Training baseline model")

    if task == "classification":
        model = DummyClassifier(strategy="most_frequent")
    else:
        model = DummyRegressor(strategy="mean")

    model.fit([[0]] * len(y), y)

    if guidance == "on":
        print("✨ Baseline model ready")

    return model
