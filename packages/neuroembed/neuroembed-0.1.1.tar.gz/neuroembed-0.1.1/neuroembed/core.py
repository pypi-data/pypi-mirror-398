from .context import ContextInjector
from .encoders.base import BaseEncoder
import numpy as np

class NeuroEmbed:
    def __init__(
        self,
        encoder: BaseEncoder,
        alpha: float = 0.7
    ):
        self.encoder = encoder
        self.contextor = ContextInjector(alpha)

    def embed(
        self,
        text: str,
        context: list[str] | None = None
    ) -> np.ndarray:

        base_emb = self.encoder.encode([text])[0]

        if context:
            ctx_embs = self.encoder.encode(context)
            return self.contextor.enrich(base_emb, ctx_embs)

        return base_emb
