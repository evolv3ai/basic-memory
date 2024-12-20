"""Base service class."""

from typing import TypeVar, Generic, List, Sequence

from basic_memory.repository.repository import Repository

T = TypeVar("T", bound=Repository)


class BaseService(Generic[T]):
    """Base service that takes a repository."""

    def __init__(self, repository: T):
        """Initialize service with repository."""
        self.repository = repository

    async def add(self, model: T) -> T:
        """Add model to repository."""
        return await self.repository.add(model)

    async def add_all(self, models: List[T]) -> Sequence[T]:
        """Add a List of models to repository."""
        return await self.repository.add_all(models)
