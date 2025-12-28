import gzip
from pathlib import Path
import struct
import urllib.request

from loguru import logger
import numpy as np
import typer

from ds_core.config import RAW_DATA_DIR

app = typer.Typer()


def download_mnist_file(url: str, filepath: Path):
    if not filepath.exists():
        logger.info(f"Downloading {filepath.name}...")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, filepath)
        logger.success(f"Downloaded {filepath.name}")
    else:
        logger.info(f"{filepath.name} already exists, skipping download")


def load_mnist_images(filepath: Path) -> np.ndarray:
    with gzip.open(filepath, "rb") as f:
        magic, num_images, rows, cols = struct.unpack(">IIII", f.read(16))
        images = np.frombuffer(f.read(), dtype=np.uint8)
        images = images.reshape(num_images, rows, cols)
    return images


def load_mnist_labels(filepath: Path) -> np.ndarray:
    with gzip.open(filepath, "rb") as f:
        magic, num_labels = struct.unpack(">II", f.read(8))
        labels = np.frombuffer(f.read(), dtype=np.uint8)
    return labels


@app.command()
def main(
    output_dir: Path = RAW_DATA_DIR,
):
    base_url = "http://yann.lecun.com/exdb/mnist/"
    files = {
        "train-images-idx3-ubyte.gz": "train_images.gz",
        "train-labels-idx1-ubyte.gz": "train_labels.gz",
        "t10k-images-idx3-ubyte.gz": "test_images.gz",
        "t10k-labels-idx1-ubyte.gz": "test_labels.gz",
    }

    logger.info("Starting MNIST dataset download...")
    output_dir.mkdir(parents=True, exist_ok=True)

    for remote_name, local_name in files.items():
        url = base_url + remote_name
        filepath = output_dir / local_name
        download_mnist_file(url, filepath)

    logger.success("MNIST dataset download complete.")

    train_images = load_mnist_images(output_dir / "train_images.gz")
    train_labels = load_mnist_labels(output_dir / "train_labels.gz")
    test_images = load_mnist_images(output_dir / "test_images.gz")
    test_labels = load_mnist_labels(output_dir / "test_labels.gz")

    logger.info(f"Train images shape: {train_images.shape}")
    logger.info(f"Train labels shape: {train_labels.shape}")
    logger.info(f"Test images shape: {test_images.shape}")
    logger.info(f"Test labels shape: {test_labels.shape}")


if __name__ == "__main__":
    app()
