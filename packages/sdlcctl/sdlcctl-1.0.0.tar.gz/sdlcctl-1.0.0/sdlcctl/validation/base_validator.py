"""
SDLC Structure Validation - Base Validator.

Abstract base class for all SDLC structure validators.
Implements plugin pattern for extensibility.

Part of Sprint 44 - SDLC Structure Scanner Engine.

Framework: SDLC 5.1.1
Epic: EP-04 - SDLC Structure Enforcement
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from .violation import ViolationReport


class BaseValidator(ABC):
    """
    Abstract base class for SDLC structure validators.

    Validators implement specific validation rules (e.g., stage naming,
    sequential numbering, header metadata). Each validator is responsible
    for one or more related rules.

    Attributes:
        VALIDATOR_ID: Unique identifier for this validator (e.g., "stage-folder")
        VALIDATOR_NAME: Human-readable name for this validator
        VALIDATOR_DESCRIPTION: Description of what this validator checks
    """

    VALIDATOR_ID: str = ""
    VALIDATOR_NAME: str = ""
    VALIDATOR_DESCRIPTION: str = ""

    def __init__(self, docs_root: Path):
        """
        Initialize validator.

        Args:
            docs_root: Root directory of SDLC documentation
        """
        if not self.VALIDATOR_ID:
            raise ValueError(f"{self.__class__.__name__} must define VALIDATOR_ID")
        if not self.VALIDATOR_NAME:
            raise ValueError(f"{self.__class__.__name__} must define VALIDATOR_NAME")

        self.docs_root = docs_root

    @abstractmethod
    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate SDLC structure.

        Args:
            paths: Optional list of specific paths to validate.
                   If None, validates entire docs_root.

        Returns:
            List of violation reports found

        Raises:
            ValidationError: If validation cannot be performed
        """
        pass

    def get_validator_info(self) -> dict:
        """Get information about this validator."""
        return {
            "id": self.VALIDATOR_ID,
            "name": self.VALIDATOR_NAME,
            "description": self.VALIDATOR_DESCRIPTION,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.VALIDATOR_ID}: {self.VALIDATOR_NAME}"


class ValidationError(Exception):
    """Exception raised when validation cannot be performed."""

    pass


class ValidatorRegistry:
    """
    Registry for SDLC structure validators.

    Manages discovery and instantiation of validators using plugin pattern.
    Validators can be registered at runtime and enabled/disabled via configuration.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._validators: dict[str, type[BaseValidator]] = {}

    def register(self, validator_class: type[BaseValidator]) -> None:
        """
        Register a validator class.

        Args:
            validator_class: Class that inherits from BaseValidator

        Raises:
            ValueError: If validator_class is not a BaseValidator subclass
            ValueError: If validator with same ID already registered
        """
        if not issubclass(validator_class, BaseValidator):
            raise ValueError(
                f"{validator_class.__name__} must inherit from BaseValidator"
            )

        validator_id = validator_class.VALIDATOR_ID
        if not validator_id:
            raise ValueError(
                f"{validator_class.__name__} must define VALIDATOR_ID class attribute"
            )

        if validator_id in self._validators:
            existing = self._validators[validator_id]
            raise ValueError(
                f"Validator '{validator_id}' already registered by {existing.__name__}"
            )

        self._validators[validator_id] = validator_class

    def unregister(self, validator_id: str) -> None:
        """
        Unregister a validator.

        Args:
            validator_id: ID of validator to unregister

        Raises:
            KeyError: If validator not found
        """
        if validator_id not in self._validators:
            raise KeyError(f"Validator '{validator_id}' not registered")

        del self._validators[validator_id]

    def get(self, validator_id: str) -> Optional[type[BaseValidator]]:
        """
        Get validator class by ID.

        Args:
            validator_id: ID of validator to retrieve

        Returns:
            Validator class if found, None otherwise
        """
        return self._validators.get(validator_id)

    def get_all(self) -> dict[str, type[BaseValidator]]:
        """
        Get all registered validators.

        Returns:
            Dictionary mapping validator IDs to validator classes
        """
        return self._validators.copy()

    def list_ids(self) -> List[str]:
        """
        List all registered validator IDs.

        Returns:
            List of validator IDs
        """
        return list(self._validators.keys())

    def create_instance(
        self, validator_id: str, docs_root: Path
    ) -> Optional[BaseValidator]:
        """
        Create validator instance.

        Args:
            validator_id: ID of validator to instantiate
            docs_root: Root directory for validator

        Returns:
            Validator instance if found, None otherwise

        Raises:
            ValidationError: If validator instantiation fails
        """
        validator_class = self.get(validator_id)
        if not validator_class:
            return None

        try:
            return validator_class(docs_root)
        except Exception as e:
            raise ValidationError(
                f"Failed to create validator '{validator_id}': {e}"
            ) from e

    def create_all_instances(
        self, docs_root: Path, validator_ids: Optional[List[str]] = None
    ) -> List[BaseValidator]:
        """
        Create instances of multiple validators.

        Args:
            docs_root: Root directory for validators
            validator_ids: Optional list of specific validator IDs to instantiate.
                          If None, creates all registered validators.

        Returns:
            List of validator instances

        Raises:
            ValidationError: If any validator instantiation fails
        """
        ids_to_create = validator_ids if validator_ids else self.list_ids()

        instances = []
        for validator_id in ids_to_create:
            instance = self.create_instance(validator_id, docs_root)
            if instance:
                instances.append(instance)
            else:
                raise ValidationError(f"Validator '{validator_id}' not found")

        return instances

    def __len__(self) -> int:
        """Number of registered validators."""
        return len(self._validators)

    def __contains__(self, validator_id: str) -> bool:
        """Check if validator is registered."""
        return validator_id in self._validators

    def __str__(self) -> str:
        """String representation."""
        return f"ValidatorRegistry({len(self._validators)} validators)"


# Global registry instance
_global_registry = ValidatorRegistry()


def get_registry() -> ValidatorRegistry:
    """Get the global validator registry."""
    return _global_registry


def register_validator(validator_class: type[BaseValidator]) -> None:
    """
    Register a validator class in the global registry.

    Args:
        validator_class: Class that inherits from BaseValidator
    """
    _global_registry.register(validator_class)


def get_validator(validator_id: str) -> Optional[type[BaseValidator]]:
    """
    Get validator class from global registry.

    Args:
        validator_id: ID of validator to retrieve

    Returns:
        Validator class if found, None otherwise
    """
    return _global_registry.get(validator_id)
