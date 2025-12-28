from pathlib import Path

from loguru import logger
import matplotlib.pyplot as plt
import numpy as np
import typer

from ds_core.config import FIGURES_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from ds_core.dataset import load_mnist_images, load_mnist_labels

app = typer.Typer()


def plot_mnist_samples(images: np.ndarray, labels: np.ndarray, n_samples: int = 10):
    fig, axes = plt.subplots(2, 5, figsize=(12, 6))
    axes = axes.ravel()

    for i in range(min(n_samples, len(images))):
        axes[i].imshow(images[i], cmap="gray")
        axes[i].set_title(f"Label: {labels[i]}")
        axes[i].axis("off")

    plt.tight_layout()
    return fig


def plot_confusion_matrix(conf_matrix: np.ndarray):
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(conf_matrix, cmap="Blues")

    ax.set_xticks(np.arange(10))
    ax.set_yticks(np.arange(10))
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title("Confusion Matrix")

    for i in range(10):
        for j in range(10):
            ax.text(j, i, conf_matrix[i, j], ha="center", va="center", color="black")

    plt.colorbar(im, ax=ax)
    plt.tight_layout()
    return fig


@app.command()
def main(
    raw_dir: Path = RAW_DATA_DIR,
    output_dir: Path = FIGURES_DIR,
    n_samples: int = 10,
):
    logger.info("Loading MNIST data...")
    train_images = load_mnist_images(raw_dir / "train_images.gz")
    train_labels = load_mnist_labels(raw_dir / "train_labels.gz")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating sample images plot...")
    fig = plot_mnist_samples(train_images, train_labels, n_samples)
    samples_path = output_dir / "mnist_samples.png"
    fig.savefig(samples_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.success(f"Saved samples plot to {samples_path}")

    predictions_path = PROCESSED_DATA_DIR / "predictions.npy"
    if predictions_path.exists():
        logger.info("Loading predictions for confusion matrix...")
        predictions = np.load(predictions_path)
        test_labels = load_mnist_labels(raw_dir / "test_labels.gz")

        from sklearn.metrics import confusion_matrix

        conf_matrix = confusion_matrix(test_labels, predictions)

        logger.info("Generating confusion matrix plot...")
        fig = plot_confusion_matrix(conf_matrix)
        conf_path = output_dir / "confusion_matrix.png"
        fig.savefig(conf_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.success(f"Saved confusion matrix to {conf_path}")
    else:
        logger.warning("Predictions not found. Run predict.py first to generate confusion matrix.")

    logger.success("Plot generation complete.")


if __name__ == "__main__":
    app()
