"""Tests for MCP delete_entities tool."""

import pytest

from basic_memory.schemas import SearchNodesResponse
from basic_memory.utils import sanitize_name


@pytest.mark.asyncio
async def test_delete_entities(server):
    """Test deleting entities."""
    # Create test entities
    entities = {
        "entities": [
            {"name": "DeleteTest1", "entity_type": "test", "observations": ["To be deleted 1"]},
            {"name": "DeleteTest2", "entity_type": "test", "observations": ["To be deleted 2"]},
        ]
    }
    await server.handle_call_tool("create_entities", entities)

    # Delete first entity
    await server.handle_call_tool(
        "delete_entities", {"entity_ids": [sanitize_name("test/DeleteTest1")]}
    )

    # Verify through search
    search_result = await server.handle_call_tool("search_nodes", {"query": "DeleteTest"})
    search_response = SearchNodesResponse.model_validate_json(search_result[0].resource.text)

    # Only second entity should remain
    assert len(search_response.matches) == 1
    assert search_response.matches[0].name == "DeleteTest2"
