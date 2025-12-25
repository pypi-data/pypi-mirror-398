import numpy as np
from sentence_transformers import SentenceTransformer
from .base import BaseEncoder

class SentenceTransformerEncoder(BaseEncoder):
    def __init__(self, model_path: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_path)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
