"""
Serilux - A powerful serialization framework for Python objects

Provides flexible serialization and deserialization capabilities with
automatic type registration and validation.
"""

from serilux.serializable import (
    Serializable,
    SerializableRegistry,
    register_serializable,
    check_serializable_constructability,
    validate_serializable_tree,
)

__all__ = [
    "Serializable",
    "SerializableRegistry",
    "register_serializable",
    "check_serializable_constructability",
    "validate_serializable_tree",
]

__version__ = "0.1.0"
