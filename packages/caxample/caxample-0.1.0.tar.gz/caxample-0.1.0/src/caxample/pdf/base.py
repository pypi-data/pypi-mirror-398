from abc import ABC, abstractmethod
import numpy as np

class BasePDF(ABC):
    @abstractmethod
    def get_weight(self, element, index: int) -> float:
        """Weight of the element. Should be normalized (sum to 1) at init time."""
        ...
    
    @abstractmethod
    def set_attributes(self, length:int)->None:
        """Set attributes"""
        ...