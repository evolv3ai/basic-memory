"""Tests for MCP schema and tool discovery."""

import pytest
from pydantic import BaseModel
from typing import List, Optional

from basic_memory.mcp.server import mcp
from basic_memory.mcp.tools.help import get_schema


class TestInput(BaseModel):
    """Test input model."""
    name: str
    value: int


class TestOutput(BaseModel):
    """Test output model."""
    result: str
    values: List[int]


@pytest.mark.asyncio
async def test_get_schema_all():
    """Test getting complete tool catalog."""
    # Create test tools
    @mcp.tool(
        name="test_tool",
        description="A test tool with enhanced metadata",
        category="test",
        examples=[{
            "name": "Basic Usage",
            "description": "Simple example",
            "code": "await test_tool({\"name\": \"test\", \"value\": 42})"
        }]
    )
    async def test_tool(request: TestInput) -> TestOutput:
        """Test tool."""
        return TestOutput(
            result=f"Processed {request.name}",
            values=[request.value]
        )

    @mcp.tool(name="basic_tool")
    async def basic_tool(value: str) -> str:
        """A basic tool without enhanced metadata"""
        return f"Echo: {value}"

    # Test schema retrieval
    catalog = await get_schema()
    
    assert "tools" in catalog
    assert "test_tool" in catalog["tools"]
    assert "basic_tool" in catalog["tools"]
    
    # Test category organization
    assert "categories" in catalog
    assert "test" in catalog["categories"]
    assert "test_tool" in catalog["categories"]["test"]["tools"]


@pytest.mark.asyncio
async def test_get_schema_enhanced_tool():
    """Test getting schema for enhanced tool."""
    @mcp.tool(
        name="test_tool",
        description="A test tool with enhanced metadata",
        category="test",
        examples=[{
            "name": "Basic Usage",
            "description": "Simple example",
            "code": "await test_tool({\"name\": \"test\", \"value\": 42})"
        }]
    )
    async def test_tool(request: TestInput) -> TestOutput:
        """Test tool."""
        return TestOutput(
            result=f"Processed {request.name}",
            values=[request.value]
        )

    schema = await get_schema("test_tool")
    
    assert "tools" in schema
    assert "test_tool" in schema["tools"]
    
    tool_info = schema["tools"]["test_tool"]
    assert tool_info["category"] == "test"
    assert len(tool_info["examples"]) == 1
    assert tool_info["input_schema"] is not None  # Updated from inputSchema
    
    # Check example format
    example = tool_info["examples"][0]
    assert example["name"] == "Basic Usage"
    assert example["description"] == "Simple example"
    assert "code" in example


@pytest.mark.asyncio
async def test_get_schema_basic_tool():
    """Test getting schema for basic tool."""
    @mcp.tool(name="basic_tool")
    async def basic_tool(value: str) -> str:
        """A basic tool without enhanced metadata"""
        return f"Echo: {value}"

    schema = await get_schema("basic_tool")
    
    assert "tools" in schema
    assert "basic_tool" in schema["tools"]
    
    tool_info = schema["tools"]["basic_tool"]
    assert tool_info["name"] == "basic_tool"
    assert tool_info["description"] == "A basic tool without enhanced metadata"
    assert "input_schema" in tool_info  # Updated from inputSchema


@pytest.mark.asyncio
async def test_get_schema_filter_examples():
    """Test filtering out examples from schema."""
    @mcp.tool(
        name="test_tool",
        description="A test tool with enhanced metadata",
        category="test",
        examples=[{
            "name": "Basic Usage",
            "description": "Simple example",
            "code": "await test_tool({\"name\": \"test\", \"value\": 42})"
        }]
    )
    async def test_tool(request: TestInput) -> TestOutput:
        """Test tool."""
        return TestOutput(
            result=f"Processed {request.name}",
            values=[request.value]
        )

    schema = await get_schema("test_tool", include_examples=False)
    assert len(schema["tools"]["test_tool"]["examples"]) == 0  # Updated to check length instead


@pytest.mark.asyncio
async def test_get_schema_unknown_tool():
    """Test getting schema for unknown tool."""
    with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
        await get_schema("unknown_tool")