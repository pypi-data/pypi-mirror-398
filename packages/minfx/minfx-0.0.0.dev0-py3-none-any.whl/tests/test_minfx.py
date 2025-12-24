import pytest
import minfx


def test_import():
    """Test that the package can be imported."""
    assert minfx is not None


def test_version():
    """Test that version is defined."""
    assert hasattr(minfx, "__version__")
    assert isinstance(minfx.__version__, str)


def test_neptune_v2_import():
    """Test that minfx.neptune_v2 can be imported."""
    import minfx.neptune_v2

    assert minfx.neptune_v2 is not None


def test_neptune_v3_import():
    """Test that minfx.neptune_v3 (neptune_scale) can be imported."""
    import minfx.neptune_v3

    assert minfx.neptune_v3 is not None
