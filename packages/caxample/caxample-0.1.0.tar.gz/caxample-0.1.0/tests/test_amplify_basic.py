import caxample as cax


def test_amplify_length_and_membership():
    examples = ["a", "b", "c"]
    f = cax.kernel.powerlaw(-1.5, window_size=10)
    g = cax.pdf.zipf(s=1.1)
    length = len(examples) * 4

    amplifier = cax.Amplifier(f, g, p=1.0, seed=123)
    out = amplifier.amplify(examples, length)
    
    assert isinstance(out, list)
    assert len(out) == length
    assert all(x in examples for x in out)


def test_amplify_deterministic_with_seed():
    examples = ["x", "y", "z"]
    f = cax.kernel.powerlaw(-1.5, window_size=10)
    g = cax.pdf.zipf(s=1.1)
    
    amplifier1 = cax.Amplifier(f, g, p=1.0, seed=42)
    out1 = amplifier1.amplify(examples, 20)
    
    amplifier2 = cax.Amplifier(f, g, p=1.0, seed=42)
    out2 = amplifier2.amplify(examples, 20)
    
    assert out1 == out2


def test_amplify_backward_compat_function():
    examples = ["a", "b", "c"]
    f = cax.kernel.powerlaw(-1.5, window_size=10)
    g = cax.pdf.zipf(s=1.1)
    length = len(examples) * 4
    
    out = cax.amplify(examples, f, g, length, p=1.0, seed=456)
    assert isinstance(out, list)
    assert len(out) == length
    assert all(x in examples for x in out)
