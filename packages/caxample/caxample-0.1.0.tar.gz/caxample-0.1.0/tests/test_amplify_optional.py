import pytest
import caxample as cax


def test_amplify_only_g_pdf():
    """Test with only g_pdf (no kernel, uniform marginal)."""
    examples = ["a", "b", "c"]
    g = cax.pdf.zipf(s=1.1)
    
    amplifier = cax.Amplifier(f_kernel=None, g_pdf=g, seed=123)
    out = amplifier.amplify(examples, 20)
    
    assert len(out) == 20
    assert all(x in examples for x in out)


def test_amplify_only_f_kernel():
    """Test with only f_kernel (uniform marginal, temporal locality)."""
    examples = ["a", "b", "c"]
    f = cax.kernel.powerlaw(-1.5, window_size=10)
    
    amplifier = cax.Amplifier(f_kernel=f, g_pdf=None, seed=456)
    out = amplifier.amplify(examples, 20)
    
    assert len(out) == 20
    assert all(x in examples for x in out)


def test_amplify_neither_raises_error():
    """Test that providing neither f nor g raises ValueError."""
    with pytest.raises(ValueError, match="At least one"):
        cax.Amplifier(f_kernel=None, g_pdf=None)


def test_amplify_both_warns():
    """Test that providing both f and g issues a warning."""
    f = cax.kernel.powerlaw(-1.5)
    g = cax.pdf.zipf()
    
    with pytest.warns(UserWarning, match="kernel creates temporal correlations"):
        cax.Amplifier(f_kernel=f, g_pdf=g)


def test_amplify_function_with_optional_params():
    """Test backward-compatible function with optional parameters."""
    examples = ["x", "y", "z"]
    g = cax.pdf.zipf(s=1.1)
    
    out = cax.amplify(examples, f_kernel=None, g_pdf=g, length=15, seed=789)
    assert len(out) == 15
    assert all(x in examples for x in out)


def test_amplify_function_requires_length():
    """Test that amplify function requires length parameter."""
    examples = ["a", "b"]
    g = cax.pdf.zipf()
    
    with pytest.raises(ValueError, match="length"):
        cax.amplify(examples, f_kernel=None, g_pdf=g, seed=111)
