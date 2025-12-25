import numpy as np
from collections import deque
import warnings

from .kernel.base import BaseKernel
from .pdf.base import BasePDF
from .pdf.uniform import UniformPDF


class Amplifier:
    """Amplify examples using kernel (temporal locality) and PDF (marginal frequency).
    
    Parameters
    ----------
    f_kernel : BaseKernel, optional
        Temporal locality kernel with normalized get_weights(t) returning weights.
        If None, always samples new values from g_pdf (no reuse).
    g_pdf : BasePDF, optional
        Marginal frequency PDF with normalized get_weight(element, index).
        If None, uses uniform distribution over examples.
    p : float, default=1.0
        Multiplier for reuse probability. Controls how much the kernel affects reuse decisions.
        p_reuse = p * sum(normalized kernel weights)
    seed : int, optional
        Random seed for reproducibility.
    
    Notes
    -----
    If both f_kernel and g_pdf are provided, be aware that the kernel introduces temporal
    correlations that may distort the marginal distribution. The observed marginal frequencies
    of the output may differ from g_pdf due to the temporal dependency structure.
    """
    
    def __init__(self, f_kernel:BaseKernel|None=None, g_pdf:BasePDF|None=None, p=1.0, seed=None):
        if f_kernel is None and g_pdf is None:
            raise ValueError("At least one of f_kernel or g_pdf must be provided")
        
        self.f_kernel = f_kernel
        if g_pdf is None:
            self.g_pdf = UniformPDF()
        else:
            self.g_pdf = g_pdf
        self.p = p
        
        if f_kernel is not None and g_pdf is not None:
            warnings.warn(
                "Both f_kernel and g_pdf are provided. The kernel creates temporal correlations "
                "that may distort the marginal distribution. The observed marginal frequencies "
                "in the output may differ from g_pdf.",
                UserWarning,
                stacklevel=2
            )
        
        self.seed(seed)
    
    def seed(self, seed=None):
        """Set or reset the random seed."""
        if seed is not None:
            np.random.seed(seed)
    
    def amplify(self, examples, length:int):
        """Generate amplified examples.
        
        Parameters
        ----------
        examples : list
            Input examples to amplify.
        length : int
            Length of output amplified examples.
        
        Returns
        -------
        list
            Amplified examples of given length.
        """
        self.g_pdf.set_attributes(length=len(examples))
        # Compute marginal weights (normalized PDF weights or uniform if g_pdf is None)

        marginal_weights = np.array(
            [self.g_pdf.get_weight(e, i) for i, e in enumerate(examples)],
            dtype=float
        )
        total = marginal_weights.sum()
        if total <= 0 or np.any(np.isnan(marginal_weights)):
            # Fall back to uniform if PDF gives no mass
            marginal_weights = np.ones(len(examples), dtype=float)
            total = marginal_weights.sum()
        marginal_weights /= total
        
        result = []
        history = deque(maxlen=getattr(self.f_kernel, "window_size", len(examples)))
        
        for t in range(length):
            reused = False
            
            # Only attempt reuse if f_kernel is provided and history exists
            if self.f_kernel is not None and len(history) > 1:
                weights = self.f_kernel.get_weights(len(history))
                if weights.size > 0:
                    p_reuse = self.p * weights.sum()
                    
                    if np.random.random() < p_reuse:
                        norm_weights = weights / weights.sum()
                        dist = np.random.choice(
                            np.arange(1, len(norm_weights) + 1), p=norm_weights
                        )
                        val = history[-dist]
                        result.append(val)
                        history.append(val)
                        reused = True
            
            if not reused:
                val = np.random.choice(examples, p=marginal_weights)
                result.append(val)
                history.append(val)
        
        return result


def amplify(examples, f_kernel=None, g_pdf=None, length=None, p=1.0, seed=None):
    """Convenience function wrapping Amplifier class.
    
    Parameters
    ----------
    examples : list
        Input examples to amplify.
    f_kernel : BaseKernel, optional
        Temporal locality kernel. If None, always samples new values from g_pdf.
    g_pdf : BasePDF, optional
        Marginal frequency PDF. If None, uses uniform distribution.
    length : int
        Length of output amplified examples.
    p : float, default=1.0
        Multiplier for reuse probability.
    seed : int, optional
        Random seed for reproducibility.
    
    Returns
    -------
    list
        Amplified examples of given length.
    """
    if length is None:
        raise ValueError("length parameter is required")
    amplifier = Amplifier(f_kernel, g_pdf, p=p, seed=seed)
    return amplifier.amplify(examples, length)