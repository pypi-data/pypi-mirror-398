from pathlib import Path
import pickle

from loguru import logger
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
import typer

from ds_core.config import MODELS_DIR, PROCESSED_DATA_DIR

app = typer.Typer()


def load_model(model_path: Path):
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model


@app.command()
def main(
    data_dir: Path = PROCESSED_DATA_DIR,
    model_path: Path = MODELS_DIR / "mnist_model.pkl",
    predictions_path: Path = PROCESSED_DATA_DIR / "predictions.npy",
):
    logger.info(f"Loading model from {model_path}...")
    model = load_model(model_path)

    logger.info("Loading test data...")
    X_test = np.load(data_dir / "X_test.npy")
    y_test = np.load(data_dir / "y_test.npy")

    logger.info(f"Test data shape: {X_test.shape}")

    logger.info("Performing inference...")
    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    logger.info(f"Test accuracy: {accuracy:.4f}")

    conf_matrix = confusion_matrix(y_test, predictions)
    logger.info("Confusion Matrix:")
    print(conf_matrix)

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(predictions_path, predictions)
    logger.success(f"Predictions saved to {predictions_path}")


if __name__ == "__main__":
    app()
