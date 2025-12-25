def fit_model(model, X_train, y_train, guidance="on"):
    if guidance == "on":
        print(f"🧠 Training {model.__class__.__name__}")

    model.fit(X_train, y_train)

    if guidance == "on":
        print("✅ Model training complete")

    return model
