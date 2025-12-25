from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

def classification_metrics(y_true, y_pred, y_prob=None, guidance="on"):
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    if y_prob is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_prob)

    if guidance == "on":
        print("📈 Classification Metrics")
        for k, v in metrics.items():
            print(f" • {k}: {v:.4f}")

        print("💡 Tip: Compare against baseline model")

    return metrics
