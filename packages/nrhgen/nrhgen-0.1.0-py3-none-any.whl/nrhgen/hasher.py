import hashlib
from pathlib import Path
from typing import Union

# Supported hashing algorithms
SUPPORTED_ALGOS = {"md5", "sha1", "sha256"}


def _validate_algo(algo: str) -> str:
    algo = algo.lower()
    if algo not in SUPPORTED_ALGOS:
        raise ValueError(f"Unsupported algorithm: {algo}")
    return algo


def hash_text(text: str, algo: str) -> str:
    """
    Generate a cryptographic hash for a text string.
    """
    algo = _validate_algo(algo)

    hasher = hashlib.new(algo)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()


def hash_file(file_path: Union[str, Path], algo: str) -> str:
    """
    Generate a cryptographic hash for a file (read in chunks).
    """
    algo = _validate_algo(algo)
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.new(algo)

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

