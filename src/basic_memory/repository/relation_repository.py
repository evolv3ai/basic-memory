"""Repository for managing Relation objects."""
from typing import Sequence, Any, Dict
from sqlalchemy import select, and_, delete

from basic_memory.models import Relation
from basic_memory.repository import Repository


class RelationRepository(Repository[Relation]):
    """Repository for Relation model with memory-specific operations."""
    
    def __init__(self, session):
        super().__init__(session, Relation)
    
    async def find_by_entities(self, from_id: str, to_id: str) -> Sequence[Relation]:
        """Find all relations between two entities."""
        query = select(Relation).filter(
            and_(
                Relation.from_id == from_id,
                Relation.to_id == to_id
            )
        )
        result = await self.execute_query(query)
        return result.scalars().all()
    
    async def find_by_type(self, relation_type: str) -> Sequence[Relation]:
        """Find all relations of a specific type."""
        query = select(Relation).filter(Relation.relation_type == relation_type)
        result = await self.execute_query(query)
        return result.scalars().all()

    async def delete_by_fields(self, **filters: Dict[str, Any]) -> bool:
        """Delete relations matching the given field values."""
        conditions = [getattr(Relation, field) == value for field, value in filters.items()]
        query = delete(Relation).where(and_(*conditions))
        result = await self.execute_query(query)
        await self.session.flush()
        return result.rowcount > 0