"""
SDLC Structure Validators.

Built-in validators for SDLC 5.1.1 structure compliance.

Part of Sprint 44 - SDLC Structure Scanner Engine.
"""

from .stage_folder import StageFolderValidator
from .sequential_numbering import SequentialNumberingValidator
from .naming_convention import NamingConventionValidator
from .header_metadata import HeaderMetadataValidator
from .cross_reference import CrossReferenceValidator

from ..base_validator import get_registry

# Auto-register validators
_registry = get_registry()
_registry.register(StageFolderValidator)
_registry.register(SequentialNumberingValidator)
_registry.register(NamingConventionValidator)
_registry.register(HeaderMetadataValidator)
_registry.register(CrossReferenceValidator)

__all__ = [
    "StageFolderValidator",
    "SequentialNumberingValidator",
    "NamingConventionValidator",
    "HeaderMetadataValidator",
    "CrossReferenceValidator",
]
