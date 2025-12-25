# tests/web/test_web_sovereignty.py
"""Litmus tests for Web sovereignty.

Web (pyfuse.web) owns browser-specific concerns:
- Compiler (pyfuse.web.compiler) - PyFuseByte bytecode generation
- DOM rendering (future)
- WASM integration (future)
"""


class TestWebSovereignty:
    """Verify Web sovereignty over browser-specific concerns."""

    def test_compiler_lives_in_web_package(self):
        """Compiler should be in pyfuse.web.compiler."""
        from pyfuse.web.compiler.pyfusebyte import compile_to_pyfusebyte

        # Compile a simple expression
        source = "x = 1 + 2"
        bytecode = compile_to_pyfusebyte(source)

        assert bytecode is not None
        assert len(bytecode) > 0

    def test_web_compiler_pyfusebyte_works(self):
        """pyfuse.web.compiler.pyfusebyte can compile expressions."""
        from pyfuse.web.compiler.pyfusebyte import compile_to_pyfusebyte

        source = "y = 3 * 4"
        bytecode = compile_to_pyfusebyte(source)

        assert bytecode is not None
        assert len(bytecode) > 0

    def test_split_brain_analyzer_in_web_compiler(self):
        """SplitBrainAnalyzer for client/server classification should be in web.compiler."""
        from pyfuse.web.compiler.analyzer import ModuleType, SplitBrainAnalyzer
        from pyfuse.web.compiler.graph import DependencyGraph

        # Create a minimal graph for the analyzer
        graph = DependencyGraph()
        analyzer = SplitBrainAnalyzer(graph)

        # Verifying it can be instantiated and module types are accessible
        assert analyzer is not None
        assert ModuleType.CLIENT is not None
        assert ModuleType.SERVER is not None

    def test_boundary_sentinel_in_web_compiler(self):
        """BoundarySentinel for bundle optimization should be in web.compiler."""
        from pyfuse.web.compiler.validator import BoundarySentinel

        # Just verifying it can be imported from the new location
        assert BoundarySentinel is not None

    def test_parallel_compiler_in_web_package(self):
        """ParallelCompiler for No-GIL compilation should be in web.compiler."""
        from pyfuse.web.compiler.parallel import ParallelCompiler, ShardedStringPool

        # Just verifying imports work from the new location
        assert ParallelCompiler is not None
        assert ShardedStringPool is not None

    def test_compiler_does_not_require_tui(self):
        """Web compiler should work without forcing TUI dependencies."""
        import sys

        # Record TUI modules before
        tui_prefixes = ("pyfuse.tui.layout", "pyfuse.tui.adapter")
        before = {m for m in sys.modules if m.startswith(tui_prefixes)}

        # Import compiler
        from pyfuse.web.compiler.pyfusebyte import compile_to_pyfusebyte

        # Compile without needing TUI
        source = "z = 5 + 5"
        bytecode = compile_to_pyfusebyte(source)

        assert bytecode is not None

        # Check that compiler didn't load new TUI modules
        after = {m for m in sys.modules if m.startswith(tui_prefixes)}
        newly_loaded = after - before

        assert not newly_loaded, f"TUI modules loaded by web compiler: {newly_loaded}"
