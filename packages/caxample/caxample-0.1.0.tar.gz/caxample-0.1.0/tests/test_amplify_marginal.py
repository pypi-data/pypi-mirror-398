import numpy as np
import caxample as cax
from caxample.pdf.base import BasePDF



class ConstPDF:
    """PDF that returns fixed weights per index to test marginal sampling."""
    def __init__(self, weights):
        self.weights = np.array(weights, dtype=float)
        total = self.weights.sum()
        if total > 0:
            self.weights /= total

    def get_weight(self, element, index: int) -> float:
        return float(self.weights[index])


def test_amplify_respects_marginal_when_no_history():
    # With window_size=1 history cannot be reused, so output should be iid from marginal
    examples = ["A", "B"]
    weights = [0.9, 0.1]
    g = ConstPDF(weights)
    f = cax.kernel.powerlaw(-1.5, window_size=1)

    length = 50
    amplifier = cax.Amplifier(f, g, p=1.0, seed=2025)
    out = amplifier.amplify(examples, length)

    # Reproduce expected sampling using numpy with same seed
    rng = np.random.RandomState(2025)
    expected = rng.choice(examples, size=length, p=np.array(weights) / np.sum(weights))

    assert out == list(expected)
