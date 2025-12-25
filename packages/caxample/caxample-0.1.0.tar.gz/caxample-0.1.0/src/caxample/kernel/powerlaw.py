from .base import BaseKernel
import numpy as np


class PowerLawKernel(BaseKernel):
    def __init__(self, alpha=-1.5, window_size=10000):
        super().__init__(window_size)
        self.alpha = alpha

    def f(self, n:int) -> float:
        return np.power(n, self.alpha)
    
