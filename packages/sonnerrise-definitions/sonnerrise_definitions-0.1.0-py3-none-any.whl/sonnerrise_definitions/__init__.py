"""Sonnerrise Definitions - Suno track generation definitions module."""

from sonnerrise_definitions.models import (
    Definition,
    DefinitionLink,
    ModelVersion,
    PersonaType,
    ServiceType,
    VocalsType,
)
from sonnerrise_definitions.repository import DefinitionRepository, DefinitionNotFoundError
from sonnerrise_definitions.schemas import (
    DefinitionCreate,
    DefinitionFilter,
    DefinitionList,
    DefinitionListItem,
    DefinitionRead,
    DefinitionUpdate,
    LinkCreate,
    LinkRead,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Definition",
    "DefinitionLink",
    "ModelVersion",
    "PersonaType",
    "ServiceType",
    "VocalsType",
    # Repository
    "DefinitionRepository",
    "DefinitionNotFoundError",
    # Schemas
    "DefinitionCreate",
    "DefinitionFilter",
    "DefinitionList",
    "DefinitionListItem",
    "DefinitionRead",
    "DefinitionUpdate",
    "LinkCreate",
    "LinkRead",
    # Version
    "__version__",
]
