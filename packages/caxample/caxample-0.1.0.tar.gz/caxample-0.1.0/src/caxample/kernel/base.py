from abc import ABC, abstractmethod
import numpy as np


class BaseKernel(ABC):
    def __init__(self, window_size: int = 10000):
        self.window_size = window_size
        self._normalized_weights_cache = {}
    
    @abstractmethod
    def f(self, n: int) -> float:
        """Mathematical f(n) proportionality. Normalization not necessary."""
        ...

    def get_weights(self, current_t: int) -> np.ndarray:
        """Returns normalized weights for distances [1, current_t-1].
        
        Caches results to avoid recomputation.
        """
        if current_t in self._normalized_weights_cache:
            return self._normalized_weights_cache[current_t]
        
        limit = min(current_t, self.window_size)
        if limit <= 1:
            result = np.array([], dtype=float)
        else:
            distances = np.arange(1, limit, dtype=int)
            weights = np.array([self.f(n) for n in distances], dtype=float)
            total = np.sum(weights)
            result = weights / total if total > 0 else weights
        
        self._normalized_weights_cache[current_t] = result
        return result
    
