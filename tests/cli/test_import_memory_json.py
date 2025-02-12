"""Tests for import_memory_json command."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from basic_memory.cli.app import app
from basic_memory.cli.commands import import_memory_json
from basic_memory.markdown import EntityParser, MarkdownProcessor

# Set up CLI runner
runner = CliRunner()


@pytest.fixture
def sample_entities():
    """Sample entities for testing."""
    return [
        {
            "type": "entity",
            "name": "test_entity",
            "entityType": "test",
            "observations": ["Test observation 1", "Test observation 2"],
        },
        {
            "type": "relation",
            "from": "test_entity",
            "to": "related_entity",
            "relationType": "test_relation",
        },
    ]


@pytest.fixture
def sample_json_file(tmp_path, sample_entities):
    """Create a sample memory.json file."""
    json_file = tmp_path / "memory.json"
    with open(json_file, "w") as f:
        for entity in sample_entities:
            f.write(json.dumps(entity) + "\n")
    return json_file


@pytest.mark.asyncio
async def test_process_memory_json(tmp_path, sample_json_file):
    """Test importing entities from JSON."""
    entity_parser = EntityParser(tmp_path)
    processor = MarkdownProcessor(entity_parser)

    results = await import_memory_json.process_memory_json(sample_json_file, tmp_path, processor)

    assert results["entities"] == 1
    assert results["relations"] == 1

    # Check file was created
    entity_file = tmp_path / "test/test_entity.md"
    assert entity_file.exists()
    content = entity_file.read_text()
    assert "Test observation 1" in content
    assert "Test observation 2" in content
    assert "test_relation [[related_entity]]" in content


@pytest.mark.asyncio
async def test_get_markdown_processor(tmp_path, monkeypatch):
    """Test getting markdown processor."""
    monkeypatch.setenv("HOME", str(tmp_path))
    processor = await import_memory_json.get_markdown_processor()
    assert isinstance(processor, MarkdownProcessor)


def test_import_json_command_file_not_found(tmp_path):
    """Test error handling for nonexistent file."""
    nonexistent = tmp_path / "nonexistent.json"
    result = runner.invoke(app, ["import-json", str(nonexistent)])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_import_json_command_success(tmp_path, sample_json_file, monkeypatch):
    """Test successful JSON import via command."""
    # Set up test environment
    monkeypatch.setenv("HOME", str(tmp_path))

    # Run import
    result = runner.invoke(app, ["import-json", str(sample_json_file)])
    assert result.exit_code == 0
    assert "Import complete" in result.output
    assert "Created 1 entities" in result.output
    assert "Added 1 relations" in result.output


def test_import_json_command_invalid_json(tmp_path):
    """Test error handling for invalid JSON."""
    # Create invalid JSON file
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("not json")

    result = runner.invoke(app, ["import-json", str(invalid_file)])
    assert result.exit_code == 1
    assert "Error during import" in result.output


def test_import_json_command_handle_old_format(tmp_path):
    """Test handling old format JSON with from_id/to_id."""
    # Create JSON with old format
    old_format = [
        {
            "type": "entity",
            "name": "test_entity",
            "entityType": "test",
            "observations": ["Test observation"],
        },
        {
            "type": "relation",
            "from_id": "test_entity",
            "to_id": "other_entity",
            "relation_type": "test_relation",
        },
    ]

    json_file = tmp_path / "old_format.json"
    with open(json_file, "w") as f:
        for item in old_format:
            f.write(json.dumps(item) + "\n")

    # Set up test environment
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("HOME", str(tmp_path))

    # Run import
    result = runner.invoke(app, ["import-json", str(json_file)])
    assert result.exit_code == 0
    assert "Import complete" in result.output
