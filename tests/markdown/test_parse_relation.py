"""Tests for the markdown entity parser."""

import pytest

from basic_memory.markdown.parser import EntityParser, ParseError


def test_parse_relation_basic():
    """Test basic relation parsing."""
    parser = EntityParser()

    rel = parser._parse_relation("- implements [[Auth Service]]")
    assert rel is not None
    assert rel.type == "implements"
    assert rel.target == "Auth Service"
    assert rel.context is None


def test_parse_relation_with_context():
    """Test relation parsing with context."""
    parser = EntityParser()

    rel = parser._parse_relation("- depends_on [[Database]] (Required for persistence)")
    assert rel is not None
    assert rel.type == "depends_on"
    assert rel.target == "Database"
    assert rel.context == "Required for persistence"


def test_parse_relation_edge_cases():
    """Test relation parsing edge cases."""
    parser = EntityParser()

    # Multiple word type
    rel = parser._parse_relation("- is used by [[Client App]] (Primary consumer)")
    assert rel is not None
    assert rel.type == "is used by"

    # Brackets in context
    rel = parser._parse_relation("- implements [[API]] (Follows [OpenAPI] spec)")
    assert rel is not None
    assert rel.context == "Follows [OpenAPI] spec"

    # Extra spaces
    rel = parser._parse_relation("-   specifies   [[Format]]   (Documentation)")
    assert rel is not None
    assert rel.type == "specifies"
    assert rel.target == "Format"


def test_parse_relation_errors():
    """Test error handling in relation parsing."""
    parser = EntityParser()

    # Missing target brackets
    with pytest.raises(ParseError, match="missing \\[\\["):
        parser._parse_relation("- implements Auth Service")

    # Unclosed target
    with pytest.raises(ParseError, match="missing ]]"):
        parser._parse_relation("- implements [[Auth Service")
