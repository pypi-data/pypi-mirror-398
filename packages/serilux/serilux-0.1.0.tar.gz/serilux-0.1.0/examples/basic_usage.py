"""
Basic usage example for Serilux.

This example demonstrates basic serialization and deserialization.
"""

from serilux import Serializable, register_serializable


@register_serializable
class Person(Serializable):
    """A simple Person class."""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.age = 0
        self.email = ""
        # Register fields to serialize
        self.add_serializable_fields(["name", "age", "email"])


def main():
    """Run the basic usage example."""
    print("=== Serilux Basic Usage Example ===\n")

    # Create a person object
    person = Person()
    person.name = "Alice"
    person.age = 30
    person.email = "alice@example.com"

    print("Original object:")
    print(f"  Name: {person.name}")
    print(f"  Age: {person.age}")
    print(f"  Email: {person.email}\n")

    # Serialize to dictionary
    data = person.serialize()
    print("Serialized data:")
    print(f"  {data}\n")

    # Deserialize from dictionary
    new_person = Person()
    new_person.deserialize(data)

    print("Deserialized object:")
    print(f"  Name: {new_person.name}")
    print(f"  Age: {new_person.age}")
    print(f"  Email: {new_person.email}\n")

    # Verify they match
    assert person.name == new_person.name
    assert person.age == new_person.age
    assert person.email == new_person.email
    print("✓ Serialization and deserialization successful!")


if __name__ == "__main__":
    main()
