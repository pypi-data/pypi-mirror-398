# caxample

Lightweight utilities to ``amplify`` sequences using a temporal kernel and marginal PDF.

## Install

```bash
pip install caxample
```

For development:

```bash
pip install -e ".[dev]"
```

## Basic usage

There are two primary entry points:

- `Amplifier` class for programmatic control
- `amplify()` convenience function

Example:

```python
from caxample.amplify import amplify, Amplifier
from caxample.kernel.powerlaw import PowerLawKernel
from caxample.pdf.zipf import ZipPDF

# Examples can be list of `any` objects.
examples = ['a', 'b', 'c', 'd','e','f','g']

# simple one-liner using defaults
out = amplify(examples, length=100, seed=42)

# more control: use a power-law temporal kernel and a Zipf marginal
kernel = PowerLawKernel(alpha=-1.5, window_size=100)
pdf = ZipPDF(s=1.2)
amp = Amplifier(f_kernel=kernel, g_pdf=pdf, p=1.0, seed=42)
out = amp.amplify(examples, length=200)

print(out[:20])
```

## Notes

- If `f_kernel` is omitted, draws are independent from the marginal `g_pdf`.
- If `g_pdf` is omitted, a uniform PDF is used.
- Supplying both `f_kernel` and `g_pdf` may produce temporal correlations that alter observed marginals (see code warnings).

## Running tests

Run the test suite with:

```bash
pytest -q
```


