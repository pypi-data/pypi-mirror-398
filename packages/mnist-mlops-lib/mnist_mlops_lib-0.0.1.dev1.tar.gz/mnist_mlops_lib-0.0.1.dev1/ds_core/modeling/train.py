import json
from pathlib import Path
import pickle

from loguru import logger
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import typer

from ds_core.config import MODELS_DIR, PROCESSED_DATA_DIR, PROJ_ROOT

app = typer.Typer()


@app.command()
def main(
    data_dir: Path = PROCESSED_DATA_DIR,
    model_path: Path = MODELS_DIR / "mnist_model.pkl",
    max_iter: int = 100,
    random_state: int = 42,
):
    logger.info("Loading preprocessed data...")
    X_train = np.load(data_dir / "X_train.npy")
    y_train = np.load(data_dir / "y_train.npy")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")

    logger.info(f"Training data shape: {X_train.shape}")
    logger.info(f"Test data shape: {X_test.shape}")

    logger.info("Training Logistic Regression model...")
    model = LogisticRegression(
        max_iter=max_iter,
        random_state=random_state,
        solver="lbfgs",
        multi_class="multinomial",
        verbose=1,
    )

    model.fit(X_train, y_train)

    logger.info("Evaluating model on training data...")
    train_pred = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, train_pred)
    logger.info(f"Training accuracy: {train_accuracy:.4f}")

    logger.info("Evaluating model on test data...")
    test_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, test_pred)
    logger.info(f"Test accuracy: {test_accuracy:.4f}")

    logger.info("\nClassification Report:")
    print(classification_report(y_test, test_pred))

    metrics = {
        "train_accuracy": float(train_accuracy),
        "test_accuracy": float(test_accuracy),
        "max_iter": max_iter,
        "random_state": random_state,
    }

    metrics_path = PROJ_ROOT / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.success(f"Model saved to {model_path}")


if __name__ == "__main__":
    app()
