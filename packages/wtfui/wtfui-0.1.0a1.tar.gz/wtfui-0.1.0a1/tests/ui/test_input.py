"""Tests for Input element text editing."""


def test_input_has_cursor_position():
    """Input should track cursor position."""
    from pyfuse.ui import Input

    inp = Input()
    assert hasattr(inp, "cursor_pos")
    assert inp.cursor_pos == 0


def test_input_has_text_value():
    """Input should track text value."""
    from pyfuse.ui import Input

    inp = Input()
    assert hasattr(inp, "text_value")
    assert inp.text_value == ""


def test_input_syncs_with_bind_signal():
    """Input text_value should sync with bind Signal."""
    from pyfuse.core.signal import Signal
    from pyfuse.ui import Input

    text = Signal("hello")
    inp = Input(bind=text)

    assert inp.text_value == "hello"


def test_input_handle_keydown_inserts_char():
    """Input should insert character on keydown."""
    from pyfuse.ui import Input

    inp = Input()
    inp.handle_keydown("a")

    assert inp.text_value == "a"
    assert inp.cursor_pos == 1


def test_input_handle_keydown_backspace():
    """Input should delete character on backspace."""
    from pyfuse.ui import Input

    inp = Input()
    inp.text_value = "hello"
    inp.cursor_pos = 5

    inp.handle_keydown("backspace")

    assert inp.text_value == "hell"
    assert inp.cursor_pos == 4
