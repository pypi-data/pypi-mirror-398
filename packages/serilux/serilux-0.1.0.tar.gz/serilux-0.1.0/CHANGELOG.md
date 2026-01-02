# Serilux Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added

- **Initial Release**: First release of Serilux serialization framework
- **Serializable Base Class**: Core `Serializable` class for object serialization
- **Automatic Type Registration**: `@register_serializable` decorator for automatic class registration
- **SerializableRegistry**: Class registry for managing serializable types
- **Nested Object Support**: Automatic serialization/deserialization of nested Serializable objects
- **List and Dictionary Support**: Automatic handling of lists and dictionaries containing Serializable objects
- **Strict Mode**: Optional strict mode for deserialization validation
- **Validation Functions**: `check_serializable_constructability` and `validate_serializable_tree` for pre-serialization validation
- **Field Management**: `add_serializable_fields` and `remove_serializable_fields` methods
- **Comprehensive Documentation**: Full Sphinx documentation with examples
- **Test Suite**: Comprehensive test coverage
- **Examples**: Practical usage examples

### Documentation

- Initial documentation structure
- API reference documentation
- User guide with examples
- Quick start guide

### Testing

- Unit tests for core functionality
- Integration tests for nested objects
- Validation tests
- Registry tests

---

**Note**: This is the initial release extracted from the Routilux project's serializable module.

