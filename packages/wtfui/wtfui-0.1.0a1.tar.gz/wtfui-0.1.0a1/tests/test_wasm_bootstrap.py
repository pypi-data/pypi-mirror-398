"""Tests for Wasm bootstrap entry point."""

from unittest.mock import MagicMock

from pyfuse.web.wasm.bootstrap import (
    PyFuseApp,
    get_document,
    get_pyodide,
    mount,
)


def test_get_document_returns_none_on_server():
    """get_document returns None when not in browser."""
    # On CPython, there's no js module
    assert get_document() is None


def test_get_pyodide_returns_none_on_server():
    """get_pyodide returns None when not in browser."""
    assert get_pyodide() is None


def test_pyfuse_app_can_be_created():
    """PyFuseApp can be instantiated with root element."""
    from pyfuse.ui import Div

    root = Div()
    app = PyFuseApp(root)
    assert app.root is root


def test_pyfuse_app_mount_uses_dom_renderer():
    """PyFuseApp.mount uses DOMRenderer in browser context."""
    from pyfuse.ui import Div

    root = Div()
    app = PyFuseApp(root)

    mock_doc = MagicMock()
    mock_container = MagicMock()
    mock_doc.getElementById.return_value = mock_container

    # Mount with mock document
    app.mount(mock_doc, container_id="pyfuse-root")

    # Should have queried for container
    mock_doc.getElementById.assert_called_once_with("pyfuse-root")


def test_mount_convenience_function():
    """mount() is a convenience wrapper for PyFuseApp."""
    from pyfuse.ui import Div

    root = Div()

    mock_doc = MagicMock()
    mock_container = MagicMock()
    mock_doc.getElementById.return_value = mock_container

    # Should not raise
    mount(root, document=mock_doc)


def test_pyfuse_app_registers_elements():
    """PyFuseApp registers elements in registry for event handling."""
    from pyfuse.ui import Button, Div

    with Div() as root:
        btn = Button("Test", on_click=lambda: None)

    app = PyFuseApp(root)

    # Registry should have elements
    assert app._registry.get(id(root)) is root
    assert app._registry.get(id(btn)) is btn
