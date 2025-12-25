from .base import BasePDF
import numpy as np

class ZipPDF(BasePDF):
    def __init__(self, s=1.1):
        self.s = s
        self.max_k = 100000
        self._zeta = self._approximate_zeta(s)
    
    def _approximate_zeta(self,s):
        """Approximate Riemann zeta function ζ(s) = Σ 1/k^s."""
        return float(np.sum([1.0 / np.power(k, s) for k in range(1, self.max_k + 1)]))

    def get_weight(self, element, index: int) -> float:
        """Return normalized Zipf probability: 1/(k^s * ζ(s))."""
        return 1.0 / (np.power(index + 1, self.s) * self._zeta)

    def set_attributes(self, length: int) -> None:
        self.max_k = length
        pass