"""Tests for PyFuseByte server endpoints."""

import pytest
from fastapi.testclient import TestClient

from pyfuse.web.compiler.writer import MAGIC_HEADER
from pyfuse.web.server.app import create_app


@pytest.fixture
def pyfusebyte_client():
    """Create test client with PyFuseByte support."""

    # Create a simple component for testing
    async def simple_app():
        from pyfuse.core.signal import Signal
        from pyfuse.ui.elements import Div, Text

        count = Signal(0)
        with Div() as root:
            Text(f"Count: {count.value}")
        return root

    app = create_app(simple_app)
    return TestClient(app)


class TestPyFuseByteEndpoint:
    """Test /app.mfbc endpoint."""

    def test_pyfusebyte_endpoint_returns_binary(self, pyfusebyte_client) -> None:
        """GET /app.mfbc returns PyFuseByte binary."""
        response = pyfusebyte_client.get("/app.mfbc")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"

    def test_pyfusebyte_starts_with_magic_header(self, pyfusebyte_client) -> None:
        """Binary starts with MYFU magic header."""
        response = pyfusebyte_client.get("/app.mfbc")

        assert response.content.startswith(MAGIC_HEADER)

    def test_pyfusebyte_cache_control(self, pyfusebyte_client) -> None:
        """Binary has appropriate cache headers for dev."""
        response = pyfusebyte_client.get("/app.mfbc")

        # In dev mode, should have no-cache or short cache
        assert "cache-control" in response.headers
        assert response.headers["cache-control"] == "no-cache, must-revalidate"
