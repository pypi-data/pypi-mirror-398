from pyfuse.web.wasm.bootstrap import (
    PyFuseApp,
    get_document,
    get_pyodide,
    mount,
)
from pyfuse.web.wasm.platform import (
    get_platform,
    is_browser,
    is_pyodide,
    is_server,
)

__all__ = [
    "PyFuseApp",
    "get_document",
    "get_platform",
    "get_pyodide",
    "is_browser",
    "is_pyodide",
    "is_server",
    "mount",
]
