"""Tests for context service."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC

from basic_memory.models import Entity, Relation, Observation, ObservationCategory
from basic_memory.services.context_service import ContextService
from basic_memory.schemas.search import SearchItemType


@pytest_asyncio.fixture
async def context_service(search_repository, entity_repository):
    """Create context service for testing."""
    return ContextService(search_repository, entity_repository)


@pytest_asyncio.fixture
async def test_graph(entity_repository, search_service):
    """Create a test knowledge graph with entities, relations and observations."""
    # Create some test entities
    entities = [
        Entity(
            title="Root Entity",
            entity_type="test",
            permalink="test/root",
            file_path="test/root.md",
            content_type="text/markdown",
        ),
        Entity(
            title="Connected Entity 1",
            entity_type="test", 
            permalink="test/connected1",
            file_path="test/connected1.md",
            content_type="text/markdown",
        ),
        Entity(
            title="Connected Entity 2",
            entity_type="test",
            permalink="test/connected2", 
            file_path="test/connected2.md",
            content_type="text/markdown",
        ),
        Entity(
            title="Deep Entity",
            entity_type="test",
            permalink="test/deep",
            file_path="test/deep.md",
            content_type="text/markdown",
        )
    ]
    entities = await entity_repository.add_all(entities)
    root, conn1, conn2, deep = entities

    # Add some observations
    root.observations = [
        Observation(content="Root note 1", category=ObservationCategory.NOTE),
        Observation(content="Root tech note", category=ObservationCategory.TECH)
    ]

    conn1.observations = [
        Observation(content="Connected 1 note", category=ObservationCategory.NOTE)
    ]

    # Add relations
    relations = [
        # Direct connections to root
        Relation(from_id=root.id, to_id=conn1.id, relation_type="connects_to"),
        Relation(from_id=conn2.id, to_id=root.id, relation_type="connected_from"),
        
        # Deep connection
        Relation(from_id=conn1.id, to_id=deep.id, relation_type="deep_connection")
    ]

    root.outgoing_relations = [relations[0]]
    conn1.outgoing_relations = [relations[2]]
    conn2.outgoing_relations = [relations[1]]

    # Save relations
    root = await entity_repository.add(root)
    conn1 = await entity_repository.add(conn1)
    conn2 = await entity_repository.add(conn2)

    # Index everything for search
    for entity in entities:
        await search_service.index_entity(entity)

    return {
        'root': root,
        'connected1': conn1,
        'connected2': conn2,
        'deep': deep,
        'observations': root.observations + conn1.observations,
        'relations': relations
    }


@pytest.mark.asyncio
async def test_find_connected_basic(context_service, test_graph, search_service):
    """Test basic connectivity traversal."""
    # Start with root entity and one of its observations
    type_id_pairs = [
        ('entity', test_graph['root'].id),
        ('observation', test_graph['observations'][0].id)
    ]
    
    results = await context_service.find_connected(type_id_pairs)

    # Verify types
    types_found = {r.type for r in results}
    assert 'entity' in types_found
    assert 'relation' in types_found
    assert 'observation' in types_found

    # Verify we found directly connected entities
    entity_ids = {r.id for r in results if r.type == 'entity'}
    assert test_graph['connected1'].id in entity_ids
    assert test_graph['connected2'].id in entity_ids

    # Verify we found observations
    assert any(
        r.type == 'observation' and "Root note 1" in r.content 
        for r in results
    )


@pytest.mark.asyncio
async def test_find_connected_depth_limit(context_service, test_graph):
    """Test depth limiting works."""
    type_id_pairs = [('entity', test_graph['root'].id)]

    # With depth=1, shouldn't find deep entity
    shallow_results = await context_service.find_connected(
        type_id_pairs,
        depth=1
    )
    shallow_entity_ids = {
        r.id for r in shallow_results 
        if r.type == 'entity'
    }
    assert test_graph['deep'].id not in shallow_entity_ids

    # With depth=2, should find deep entity
    deep_results = await context_service.find_connected(
        type_id_pairs,
        depth=2
    )
    deep_entity_ids = {
        r.id for r in deep_results 
        if r.type == 'entity'
    }
    assert test_graph['deep'].id in deep_entity_ids


@pytest.mark.asyncio
async def test_find_connected_timeframe(context_service, test_graph, search_repository):
    """Test timeframe filtering."""
    now = datetime.now(UTC)
    old_date = now - timedelta(days=10)
    recent_date = now - timedelta(days=1)

    # Set created_at for entities and reindex
    test_graph['root'].created_at = old_date
    test_graph['connected1'].created_at = recent_date

    await search_repository.index_item(
        id=test_graph['root'].id,
        title=test_graph['root'].title,
        content="Root content",
        permalink=test_graph['root'].permalink,
        file_path=test_graph['root'].file_path,
        type='entity',
        metadata={"created_at": old_date.isoformat()},
    )
    
    await search_repository.index_item(
        id=test_graph['connected1'].id,
        title=test_graph['connected1'].title,
        content="Connected 1 content",
        permalink=test_graph['connected1'].permalink,
        file_path=test_graph['connected1'].file_path,
        type='entity',
        metadata={"created_at": recent_date.isoformat()},
    )

    type_id_pairs = [('entity', test_graph['root'].id)]

    # Search with a 7-day cutoff
    since_date = now - timedelta(days=7)
    results = await context_service.find_connected(
        type_id_pairs,
        since=since_date
    )

    # Should only find recent entities
    entity_ids = {r.id for r in results if r.type == 'entity'}
    assert test_graph['connected1'].id in entity_ids  # Recent entity
    assert test_graph['root'].id not in entity_ids    # Old entity excluded by timeframe


@pytest.mark.asyncio
async def test_find_connected_from_mixed_types(context_service, test_graph):
    """Test finding connections starting from different types."""
    # Start with a mix of observation and relation
    type_id_pairs = [
        ('observation', test_graph['observations'][0].id),
        ('relation', test_graph['relations'][0].id)
    ]

    results = await context_service.find_connected(type_id_pairs)

    # Should find the parent entity and connected items
    entity_ids = {r.id for r in results if r.type == 'entity'}
    assert test_graph['root'].id in entity_ids  # Parent of observation
    assert test_graph['connected1'].id in entity_ids  # Connected through relation