import numpy as np
import fasttext
from .base import BaseEncoder

class FastTextEncoder(BaseEncoder):
    def __init__(self, model_path: str):
        self.model = fasttext.load_model(model_path)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = [self.model.get_sentence_vector(t) for t in texts]
        vectors = np.array(vectors)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / norms
