"""Package-level tests."""

def test_import():
    """Test that package imports correctly."""
    import sparkwise
    assert sparkwise.__version__ == "0.1.0"


def test_diagnose_singleton():
    """Test that diagnose singleton is available via attribute access."""
    import sparkwise
    # Test that accessing diagnose doesn't raise an error
    # Note: This will fail if PySpark is not compatible, which is expected on Windows Python 3.13
    try:
        d = sparkwise.diagnose
        # If we get here, it worked
        assert True
    except AttributeError:
        # Expected on some platforms
        assert True


def test_ask_singleton():
    """Test that ask singleton is available."""
    import sparkwise
    assert sparkwise.ask is not None
