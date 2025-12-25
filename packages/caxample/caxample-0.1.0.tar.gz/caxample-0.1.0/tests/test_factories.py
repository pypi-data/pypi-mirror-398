import caxample as cax
from caxample.kernel.powerlaw import PowerLawKernel
from caxample.pdf.zipf import ZipPDF


def test_kernel_factories():
    k1 = cax.kernel.powerlaw(-1.5)
    assert isinstance(k1, PowerLawKernel)

    k2 = cax.kernel.getKernel("powerlaw", alpha=-1.5)
    assert isinstance(k2, PowerLawKernel)


def test_pdf_factories():
    p1 = cax.pdf.zipf(s=1.1)
    assert isinstance(p1, ZipPDF)

    p2 = cax.pdf.getPDF("zipf", s=1.1)
    assert isinstance(p2, ZipPDF)
