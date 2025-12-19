from dataclasses import dataclass
from typing import List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class EmbeddingIndex:
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __post_init__(self) -> None:
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.embeddings = None

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype="float32")

    def build(self, texts: List[str]) -> None:
        vectors = self.encode(texts)
        self.embeddings = vectors
        dimension = vectors.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(vectors)

    def search(self, query_vectors: np.ndarray, top_k: int = 5):
        if self.index is None:
            raise ValueError("Index is not built. Call build() first.")
        distances, indices = self.index.search(query_vectors, top_k)
        return distances, indices
