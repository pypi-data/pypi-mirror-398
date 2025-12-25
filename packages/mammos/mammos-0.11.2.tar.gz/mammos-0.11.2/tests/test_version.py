import mammos


def test_version():
    """Check that __version__ exists and is a string."""
    assert isinstance(mammos.__version__, str)
