from .base import BasePDF
import numpy as np


class UniformPDF(BasePDF):
    """Uniform probability distribution over elements."""

    def __init__(self, n_elements=None):
        """Initialize uniform PDF.
        
        Parameters
        ----------
        n_elements : int, optional
            Number of elements. If provided, precomputes uniform weight.
            Otherwise computed dynamically based on index.
        """
        self.n_elements = n_elements

    def set_attributes(self, length: int) -> None:
        self.n_elements = length
        pass

    def get_weight(self, element, index: int) -> float:
        """Return uniform weight: 1/n_elements or 1.0 if n_elements is unknown."""
        if self.n_elements is not None:
            return 1.0 / self.n_elements
        return 1.0
