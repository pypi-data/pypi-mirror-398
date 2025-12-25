def evaluation_summary(metrics, task="classification", guidance="on"):
    if guidance == "off":
        return

    print("🧭 Evaluation Summary")

    if task == "classification":
        if metrics.get("f1", 0) < 0.6:
            print("⚠️ Low F1-score → try feature engineering or class balancing")
        else:
            print("✅ Model performance is reasonable")

    else:
        if metrics.get("R2", 0) < 0.5:
            print("⚠️ Low R² → consider nonlinear models or feature interactions")
        else:
            print("✅ Regression fit looks acceptable")
