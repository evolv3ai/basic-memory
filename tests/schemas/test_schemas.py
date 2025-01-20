"""Tests for Pydantic schema validation and conversion."""

import pytest
from pydantic import ValidationError, BaseModel

from basic_memory.schemas import (
    Entity,
    EntityResponse,
    Relation,
    CreateEntityRequest,
    SearchNodesRequest,
    GetEntitiesRequest,
    RelationResponse,
)
from basic_memory.schemas.base import to_snake_case, TimeFrame


def test_entity_in_minimal():
    """Test creating EntityIn with minimal required fields."""
    data = {"title": "test_entity", "entity_type": "knowledge"}
    entity = Entity.model_validate(data)
    assert entity.title == "test_entity"
    assert entity.entity_type == "knowledge"
    assert entity.summary is None
    assert entity.observations == []


def test_entity_in_complete():
    """Test creating EntityIn with all fields."""
    data = {
        "title": "test_entity",
        "entity_type": "knowledge",
        "summary": "A test entity",
        "observations": ["Test observation"],
    }
    entity = Entity.model_validate(data)
    assert entity.title == "test_entity"
    assert entity.entity_type == "knowledge"
    assert entity.summary == "A test entity"
    assert len(entity.observations) == 1
    assert entity.observations[0] == "Test observation"


def test_entity_in_validation():
    """Test validation errors for EntityIn."""
    with pytest.raises(ValidationError):
        Entity.model_validate({"file_path": "test"})  # Missing required fields

    with pytest.raises(ValidationError):
        Entity.model_validate({"title": "test"})  # Missing entityType

    with pytest.raises(ValidationError):
        Entity.model_validate({"entityType": "test"})  # Missing name


def test_relation_in_validation():
    """Test RelationIn validation."""
    data = {"from_id": "test/123", "to_id": "test/456", "relation_type": "test"}
    relation = Relation.model_validate(data)
    assert relation.from_id == "test/123"
    assert relation.to_id == "test/456"
    assert relation.relation_type == "test"
    assert relation.context is None

    # With context
    data["context"] = "test context"
    relation = Relation.model_validate(data)
    assert relation.context == "test context"

    # Missing required fields
    with pytest.raises(ValidationError):
        Relation.model_validate({"from_id": "123", "to_id": "456"})  # Missing relationType


def test_relation_response():
    """Test RelationResponse validation."""
    data = {
        "from_id": "test/123",
        "to_id": "test/456",
        "relation_type": "test",
        "from_entity": {"permalink": "test/123"},
        "to_entity": {"permalink": "test/456"},
    }
    relation = RelationResponse.model_validate(data)
    assert relation.from_id == "test/123"
    assert relation.to_id == "test/456"
    assert relation.relation_type == "test"
    assert relation.context is None


def test_create_entities_input():
    """Test CreateEntitiesInput validation."""
    data = {
        "entities": [
            {"title": "entity1", "entity_type": "knowledge"},
            {"title": "entity2", "entity_type": "knowledge", "summary": "test description"},
        ]
    }
    create_input = CreateEntityRequest.model_validate(data)
    assert len(create_input.entities) == 2
    assert create_input.entities[1].summary == "test description"

    # Empty entities list should fail
    with pytest.raises(ValidationError):
        CreateEntityRequest.model_validate({"entities": []})


def test_entity_out_from_attributes():
    """Test EntityOut creation from database model attributes."""
    # Simulate database model attributes
    db_data = {
        "permalink": "test/test",
        "title": "test",
        "entity_type": "knowledge",
        "content_type": "text/markdown",
        "summary": "test description",
        "observations": [{"id": 1, "content": "test obs", "context": None}],
        "relations": [
            {
                "id": 1,
                "from_id": "test/test",
                "to_id": "test/test",
                "relation_type": "test",
                "context": None,
            }
        ],
    }
    entity = EntityResponse.model_validate(db_data)
    assert entity.permalink == "test/test"
    assert entity.summary == "test description"
    assert len(entity.observations) == 1
    assert len(entity.relations) == 1


def test_optional_fields():
    """Test handling of optional fields."""
    # Create with no optional fields
    entity = Entity.model_validate({"title": "test", "entity_type": "knowledge"})
    assert entity.summary is None
    assert entity.observations == []

    # Create with empty optional fields
    entity = Entity.model_validate(
        {
            "title": "test",
            "entity_type": "knowledge",
            "summary": None,
            "observations": [],
        }
    )
    assert entity.summary is None
    assert entity.observations == []

    # Create with some optional fields
    entity = Entity.model_validate(
        {"title": "test", "entity_type": "knowledge", "summary": "test", "observations": []}
    )
    assert entity.summary == "test"
    assert entity.observations == []


def test_search_nodes_input():
    """Test SearchNodesInput validation."""
    search = SearchNodesRequest.model_validate({"query": "test query"})
    assert search.query == "test query"

    with pytest.raises(ValidationError):
        SearchNodesRequest.model_validate({})  # Missing required query


def test_open_nodes_input():
    """Test OpenNodesInput validation."""
    open_input = GetEntitiesRequest.model_validate({"permalinks": ["test/test", "test/test2"]})
    assert len(open_input.permalinks) == 2

    # Empty names list should fail
    with pytest.raises(ValidationError):
        GetEntitiesRequest.model_validate({"permalinks": []})


def test_path_sanitization():
    """Test to_snake_case() handles various inputs correctly."""
    test_cases = [
        ("BasicMemory", "basic_memory"),  # CamelCase
        ("Memory Service", "memory_service"),  # Spaces
        ("memory-service", "memory_service"),  # Hyphens
        ("Memory_Service", "memory_service"),  # Already has underscore
        ("API2Service", "api2_service"),  # Numbers
        ("  Spaces  ", "spaces"),  # Extra spaces
        ("mixedCase", "mixed_case"),  # Mixed case
        ("snake_case_already", "snake_case_already"),  # Already snake case
        ("ALLCAPS", "allcaps"),  # All caps
        ("with.dots", "with_dots"),  # Dots
    ]

    for input_str, expected in test_cases:
        result = to_snake_case(input_str)
        assert result == expected, f"Failed for input: {input_str}"


def test_permalink_generation():
    """Test permalink property generates correct paths."""
    test_cases = [
        ({"title": "BasicMemory", "entity_type": "knowledge"}, "basic-memory"),
        ({"title": "Memory Service", "entity_type": "knowledge"}, "memory-service"),
        ({"title": "API Gateway", "entity_type": "knowledge"}, "api-gateway"),
        ({"title": "TestCase1", "entity_type": "knowledge"}, "test-case1"),
    ]

    for input_data, expected_path in test_cases:
        entity = Entity.model_validate(input_data)
        assert entity.permalink == expected_path, f"Failed for input: {input_data}"


@pytest.mark.parametrize(
    "timeframe,expected_valid",
    [
        ("7d", True),
        ("yesterday", True),
        ("2 days ago", True),
        ("last week", True),
        ("3 weeks ago", True),
        ("invalid", False),
        ("tomorrow", False),
        ("next week", False),
        ("", False),
        ("0d", True),
    ],
)
def test_timeframe_validation(timeframe: str, expected_valid: bool):
    """Test TimeFrame validation directly."""

    class TimeFrameModel(BaseModel):
        timeframe: TimeFrame

    if expected_valid:
        try:
            tf = TimeFrameModel.model_validate({"timeframe": timeframe})
            assert isinstance(tf.timeframe, str)
        except ValueError as e:
            pytest.fail(f"TimeFrame failed to validate '{timeframe}' with error: {e}")
    else:
        with pytest.raises(ValueError):
            tf = TimeFrameModel.model_validate({"timeframe": timeframe})
