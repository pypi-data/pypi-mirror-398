
from .powerlaw import PowerLawKernel

def powerlaw(alpha=-1.5, window_size=10000):
    return PowerLawKernel(alpha, window_size=window_size)

def getKernel(name: str, **kwargs):
    name = name.lower()
    if name == "powerlaw":
        return PowerLawKernel(**kwargs)
    raise ValueError(f"Unknown kernel: {name}")