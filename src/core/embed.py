"""Multilingual sentence embeddings for retrieval."""

from __future__ import annotations

import os

# Avoid TensorFlow/Keras import issues on Windows; sentence-transformers uses PyTorch.
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import numpy as np

from src.config import EMBEDDING_MODEL

_CACHE: dict[tuple[str, bool], "Embedder"] = {}


class Embedder:
    def __init__(self, model_name: str = EMBEDDING_MODEL, *, local_files_only: bool = False) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name, local_files_only=local_files_only)

    def encode(self, texts: list[str], *, show_progress: bool = False) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
        )
        return np.asarray(vectors, dtype=np.float32)

    @property
    def dimension(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())


def get_embedder(model_name: str = EMBEDDING_MODEL, *, local_files_only: bool = False) -> Embedder:
    key = (model_name, local_files_only)
    if key not in _CACHE:
        _CACHE[key] = Embedder(model_name, local_files_only=local_files_only)
    return _CACHE[key]
