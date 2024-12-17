"""Knowledge graph schema exports.

This module exports all schema classes to simplify imports.
Rather than importing from individual schema files, you can
import everything from basic_memory.schemas.
"""

# Base types and models
from basic_memory.schemas.base import (
    Observation,
    EntityType,
    RelationType,
    EntityId,
    Relation,
    Entity,
)

# Request models
from basic_memory.schemas.request import (
    AddObservationsRequest,
    CreateEntityRequest,
    SearchNodesRequest,
    OpenNodesRequest,
    CreateRelationsRequest,
)

# Response models
from basic_memory.schemas.response import (
    SQLAlchemyModel,
    ObservationResponse,
    ObservationsResponse,
    RelationResponse,
    EntityResponse,
    CreateEntityResponse,
    SearchNodesResponse,
    OpenNodesResponse,
    AddObservationsResponse,
    CreateRelationsResponse,
    DeleteEntityResponse,
    DeleteRelationsResponse,
    DeleteObservationsResponse,
)

# Delete operation models
from basic_memory.schemas.delete import (
    DeleteEntityRequest,
    DeleteRelationsRequest,
    DeleteObservationsRequest,
)

# For convenient imports, export all models
__all__ = [
    # Base
    "Observation",
    "EntityType",
    "RelationType", 
    "EntityId",
    "Relation",
    "Entity",
    
    # Requests
    "AddObservationsRequest",
    "CreateEntityRequest",
    "SearchNodesRequest",
    "OpenNodesRequest",
    "CreateRelationsRequest",
    
    # Responses
    "SQLAlchemyModel",
    "ObservationResponse",
    "ObservationsResponse",
    "RelationResponse",
    "EntityResponse",
    "CreateEntityResponse",
    "SearchNodesResponse",
    "OpenNodesResponse",
    "AddObservationsResponse",
    "CreateRelationsResponse",
    "DeleteEntityResponse",
    "DeleteRelationsResponse",
    "DeleteObservationsResponse",
    
    # Delete Operations
    "DeleteEntityRequest",
    "DeleteRelationsRequest",
    "DeleteObservationsRequest",
]