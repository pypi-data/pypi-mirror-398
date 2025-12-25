("""PDF factories and registry for caxample.

Expose simple constructors like `zipf()` and a `getPDF(name, **kwargs)` helper.
""")

from .zipf import ZipPDF
from .uniform import UniformPDF

def zipf(s=1.1):
    return ZipPDF(s=s)

def uniform(n_elements=None):
    return UniformPDF(n_elements=n_elements)

def getPDF(name: str, **kwargs):
    name = name.lower()
    if name == "zipf":
        return ZipPDF(**kwargs)
    elif name == "uniform":
        return UniformPDF(**kwargs)
