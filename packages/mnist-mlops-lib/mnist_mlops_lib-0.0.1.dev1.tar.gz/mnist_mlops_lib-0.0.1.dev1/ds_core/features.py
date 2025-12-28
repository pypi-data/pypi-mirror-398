from pathlib import Path

from loguru import logger
import numpy as np
import typer

from ds_core.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from ds_core.dataset import load_mnist_images, load_mnist_labels

app = typer.Typer()


def normalize_images(images: np.ndarray) -> np.ndarray:
    return images.astype(np.float32) / 255.0


def flatten_images(images: np.ndarray) -> np.ndarray:
    return images.reshape(images.shape[0], -1)


def preprocess_mnist(images: np.ndarray) -> np.ndarray:
    normalized = normalize_images(images)
    flattened = flatten_images(normalized)
    return flattened


@app.command()
def main(
    raw_dir: Path = RAW_DATA_DIR,
    output_dir: Path = PROCESSED_DATA_DIR,
):
    logger.info("Loading MNIST data...")
    train_images = load_mnist_images(raw_dir / "train_images.gz")
    train_labels = load_mnist_labels(raw_dir / "train_labels.gz")
    test_images = load_mnist_images(raw_dir / "test_images.gz")
    test_labels = load_mnist_labels(raw_dir / "test_labels.gz")

    logger.info("Preprocessing MNIST images...")
    X_train = preprocess_mnist(train_images)
    X_test = preprocess_mnist(test_images)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Saving processed data...")
    np.save(output_dir / "X_train.npy", X_train)
    np.save(output_dir / "y_train.npy", train_labels)
    np.save(output_dir / "X_test.npy", X_test)
    np.save(output_dir / "y_test.npy", test_labels)

    logger.info(f"Train features shape: {X_train.shape}")
    logger.info(f"Train labels shape: {train_labels.shape}")
    logger.info(f"Test features shape: {X_test.shape}")
    logger.info(f"Test labels shape: {test_labels.shape}")
    logger.success("Features generation complete.")


if __name__ == "__main__":
    app()
