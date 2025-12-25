__all__ = ["ConsoleRenderer", "LayoutAdapter", "ReactiveLayoutAdapter", "RenderTreeBuilder"]


def __getattr__(name: str):
    if name == "ConsoleRenderer":
        from pyfuse.tui.renderer import ConsoleRenderer

        return ConsoleRenderer
    if name == "LayoutAdapter":
        from pyfuse.tui.adapter import LayoutAdapter

        return LayoutAdapter
    if name == "ReactiveLayoutAdapter":
        from pyfuse.tui.adapter import ReactiveLayoutAdapter

        return ReactiveLayoutAdapter
    if name == "RenderTreeBuilder":
        from pyfuse.tui.builder import RenderTreeBuilder

        return RenderTreeBuilder
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
