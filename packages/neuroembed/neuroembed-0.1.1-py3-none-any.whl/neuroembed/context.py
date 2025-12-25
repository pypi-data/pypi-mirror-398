# neuroembed/context.py
import numpy as np

class ContextInjector:
    def __init__(self, alpha: float = 0.7):
        self.alpha = alpha

    def enrich(
        self,
        base_embedding: np.ndarray,
        context_embeddings: np.ndarray | None
    ) -> np.ndarray:

        if context_embeddings is None or len(context_embeddings) == 0:
            return base_embedding

        context_mean = np.mean(context_embeddings, axis=0)

        enriched = (
            self.alpha * base_embedding +
            (1 - self.alpha) * context_mean
        )

        return enriched / np.linalg.norm(enriched)
