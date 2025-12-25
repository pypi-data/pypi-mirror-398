def predict(model, X, proba=False, guidance="on"):
    if guidance == "on":
        print("🔮 Generating predictions")

    if proba and hasattr(model, "predict_proba"):
        preds = model.predict_proba(X)
    else:
        preds = model.predict(X)

    if guidance == "on":
        print("✨ Prediction complete")

    return preds
