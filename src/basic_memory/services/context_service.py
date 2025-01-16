"""Service for building rich context from the knowledge graph."""

from datetime import datetime, UTC, timezone
from typing import List, Optional, Tuple
from loguru import logger
from sqlalchemy import text

from basic_memory.repository.search_repository import SearchRepository
from basic_memory.repository.entity_repository import EntityRepository
from basic_memory.schemas.memory import MemoryUrl
from basic_memory.schemas.search import SearchQuery, SearchItemType


class ContextService:
    """Service for building rich context from memory:// URIs.

    Handles three types of context building:
    1. Direct permalink lookup - exact match on path
    2. Pattern matching - using * wildcards
    3. Special modes via params (e.g., 'related')
    """

    def __init__(
            self,
            search_repository: SearchRepository,
            entity_repository: EntityRepository,
    ):
        self.search_repository = search_repository
        self.entity_repository = entity_repository

    async def build_context(
            self,
            uri: str,
            depth: int = 2,
            since: Optional[datetime] = None,
    ):
        """Build rich context from a memory:// URI."""
        logger.debug(f"Building context for URI {uri}")

        # Parse the URI
        memory_url = MemoryUrl.parse(uri)

        # Find primary entities based on URL type
        if memory_url.params.get("type") == "related":
            # Special mode for finding related content
            target = memory_url.params["target"]
            primary = await self.find_related(target)
        elif memory_url.pattern:
            # Pattern matching with *
            primary = await self.find_by_pattern(memory_url.pattern)
        else:
            # Direct permalink lookup
            primary = await self.find_by_permalink(memory_url.relative_path())

        # Get type_id pairs for traversal
        type_id_pairs = [(r.type, r.id) for r in primary] if primary else []

        # Find connected content
        related = await self.find_connected(
            type_id_pairs,
            max_depth=depth,
            since=since
        )

        # Build response
        return {
            "primary_entities": primary,
            "related_entities": related,
            "metadata": {
                "uri": uri,
                "depth": depth,
                "timeframe": since.isoformat() if since else None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "matched_entities": len(primary),
                "total_entities": len(primary) + len(related),
                "total_relations": sum(1 for r in related if r.type == SearchItemType.RELATION)
            }
        }

    async def find_by_pattern(self, pattern: str):
        """Find entities matching a pattern with * wildcards."""
        query = SearchQuery(permalink_pattern=pattern)
        return await self.search_repository.search(query)

    async def find_by_permalink(self, permalink: str):
        """Find an entity by exact permalink."""
        query = SearchQuery(permalink=permalink)
        return await self.search_repository.search(query)

    async def find_related(self, permalink: str):
        """Find entities related to a given permalink."""
        # First find the target entity
        target = await self.find_by_permalink(permalink)
        if not target:
            return []
            
        # Use find_connected to get related items
        type_id_pairs = [(r.type.value, r.id) for r in target]
        return await self.find_connected(
            type_id_pairs,
            max_depth=1  # Only immediate relations
        )

    async def find_connected(
            self,
            type_id_pairs: List[Tuple[str, int]],
            max_depth: int = 2,
            since: Optional[datetime] = None,
    ):
        """Find items connected through relations.

        Uses recursive CTE to find:
        - Connected entities
        - Their observations
        - Relations that connect them
        """
        if not type_id_pairs:
            return []
            
        logger.debug(f"Finding connected items for {type_id_pairs} with depth {max_depth}")

        # Build the VALUES clause directly since SQLite doesn't handle parameterized IN well
        values = ", ".join([f"('{t}', {i})" for t, i in type_id_pairs])

        # Parameters for bindings
        params = {"max_depth": max_depth}
        if since:
            params["since_date"] = since.isoformat()

        # Build date filter
        date_filter = f"AND base.created_at >= :since_date" if since else ""
        r1_date_filter = f"AND r1.created_at >= :since_date" if since else ""
        related_date_filter = f"AND related.created_at >= :since_date" if since else ""

        query = text(f"""
            WITH RECURSIVE context_graph AS (
                -- Base case: seed items
                SELECT 
                    id,
                    type,
                    title, 
                    permalink,
                    from_id,
                    to_id,
                    relation_type,
                    category,
                    entity_id,
                    content,
                    0 as depth,
                    id as root_id,
                    created_at
                FROM search_index base
                WHERE (base.type, base.id) IN ({values})
                {date_filter}

                UNION 

                -- Find relations and their connected items at each depth
                SELECT
                    related.id,
                    related.type,
                    related.title,
                    related.permalink,
                    related.from_id,
                    related.to_id,
                    related.relation_type,
                    related.category,
                    related.entity_id,
                    related.content,
                    cg.depth + 1,
                    cg.root_id,
                    related.created_at
                FROM context_graph cg
                JOIN search_index r1 ON (
                    -- First find the relations
                    cg.type = 'entity' AND 
                    r1.type = 'relation' AND 
                    (r1.from_id = cg.id OR r1.to_id = cg.id)
                    {r1_date_filter}
        )
                -- Then join to ALL related items at the same depth 
                JOIN search_index related ON (
                    -- The found relation 
                    related.id = r1.id
                    OR
                    -- The entity it connects to
                    (related.type = 'entity' AND 
                     (related.id = r1.from_id OR related.id = r1.to_id))
                    OR
                    -- Any observations that are relevant
                    (related.type = 'observation' AND 
                     (related.entity_id = r1.from_id OR related.entity_id = r1.to_id))
                    {related_date_filter}
                )
                WHERE cg.depth < :max_depth
            )
            -- Select shortest path to each item
            SELECT DISTINCT 
                type,
                id,
                title,
                permalink,
                from_id,
                to_id,
                relation_type,
                category,
                entity_id,
                content,
                MIN(depth) as depth,
                root_id,
                created_at
            FROM context_graph
            GROUP BY
                type, id, title, permalink, from_id, to_id,
                relation_type, category, entity_id, content,
                root_id, created_at
            ORDER BY depth, type, id
        """)
        
        results = await self.search_repository.execute_query(query, params=params)
        return results.all()