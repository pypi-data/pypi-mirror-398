"""Test renderers can be imported from pyfuse.web."""


def test_html_renderer_import_from_web():
    """HTMLRenderer should be importable from pyfuse.web."""
    from pyfuse.web import HTMLRenderer

    assert HTMLRenderer is not None


def test_dom_renderer_import_from_web():
    """DOMRenderer should be importable from pyfuse.web."""
    from pyfuse.web import DOMRenderer

    assert DOMRenderer is not None


def test_html_renderer_renders():
    """HTMLRenderer from pyfuse.web should render."""
    from pyfuse.core.protocol import RenderNode
    from pyfuse.web import HTMLRenderer

    renderer = HTMLRenderer()
    node = RenderNode(tag="div", element_id=1, props={}, children=[])
    html = renderer.render_node(node)

    assert "<div" in html
