# tests/test_exports.py
"""Tests for core package exports."""


def test_core_exports():
    """Core classes are exported from pyfuse package."""
    from pyfuse import Effect, Element, Signal

    assert Element is not None
    assert Signal is not None
    assert Effect is not None


def test_signal_can_be_used():
    """Signal works when imported from pyfuse."""
    from pyfuse import Signal

    sig = Signal(42)
    assert sig.value == 42
