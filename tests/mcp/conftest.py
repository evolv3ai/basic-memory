"""Tests for the MCP server implementation using FastAPI TestClient."""

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from mcp.server import FastMCP

from basic_memory.api.app import app as fastapi_app
from basic_memory.deps import get_project_config, get_engine_factory
from basic_memory.services.search_service import SearchService
from basic_memory.mcp.server import mcp as mcp_server


@pytest.fixture
def mcp() -> FastMCP:
    return mcp_server


@pytest_asyncio.fixture
def app(test_config, engine_factory) -> FastAPI:
    """Create test FastAPI application."""
    app = fastapi_app
    app.dependency_overrides[get_project_config] = lambda: test_config
    app.dependency_overrides[get_engine_factory] = lambda: engine_factory
    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create test client that both MCP and tests will use."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
def test_entity_data():
    """Sample data for creating a test entity."""
    return {
        "entities": [
            {
                "title": "Test Entity",
                "entity_type": "test",
                "summary": "",  # Empty string instead of None
            }
        ]
    }


@pytest_asyncio.fixture(autouse=True)
async def init_search_index(search_service: SearchService):
    await search_service.init_search_index()
