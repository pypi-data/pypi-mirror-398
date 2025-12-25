from abc import ABC, abstractmethod
import numpy as np

class BaseEncoder(ABC):

    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        pass
