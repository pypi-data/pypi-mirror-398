"""Test ConsoleRenderer can be imported from pyfuse.tui."""


def test_console_renderer_import_from_tui():
    """ConsoleRenderer should be importable from pyfuse.tui."""
    from pyfuse.tui import ConsoleRenderer

    assert ConsoleRenderer is not None


def test_console_renderer_renders():
    """ConsoleRenderer from pyfuse.tui should render."""
    from pyfuse.core.protocol import RenderNode
    from pyfuse.tui import ConsoleRenderer

    renderer = ConsoleRenderer(width=80, height=24)
    node = RenderNode(tag="div", element_id=1, props={}, children=[])
    renderer.render_node(node)
    output = renderer.flush()

    assert output is not None
