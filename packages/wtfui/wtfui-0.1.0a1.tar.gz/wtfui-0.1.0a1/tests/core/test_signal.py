"""Test Signal can be imported from pyfuse.core."""


def test_signal_import_from_core():
    """Signal should be importable from pyfuse.core."""
    from pyfuse.core import Signal

    assert Signal is not None


def test_signal_basic_from_core():
    """Signal from core should work identically to pyfuse.signal."""
    from pyfuse.core import Signal

    sig = Signal(42)
    assert sig.value == 42

    sig.value = 100
    assert sig.value == 100
