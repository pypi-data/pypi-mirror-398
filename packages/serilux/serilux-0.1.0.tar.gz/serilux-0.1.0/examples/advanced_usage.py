"""
Advanced usage example for Serilux.

This example demonstrates:
- Nested Serializable objects
- Lists containing Serializable objects
- Dictionaries containing Serializable objects
- Validation
"""

from serilux import (
    Serializable,
    register_serializable,
    validate_serializable_tree,
)


@register_serializable
class Address(Serializable):
    """An Address class."""

    def __init__(self):
        super().__init__()
        self.street = ""
        self.city = ""
        self.state = ""
        self.zip_code = ""
        self.add_serializable_fields(["street", "city", "state", "zip_code"])


@register_serializable
class Person(Serializable):
    """A Person class with an address."""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.age = 0
        self.address = None
        self.add_serializable_fields(["name", "age", "address"])


@register_serializable
class Team(Serializable):
    """A Team class containing multiple people."""

    def __init__(self):
        super().__init__()
        self.name = ""
        self.members = []  # List of Person objects
        self.roles = {}  # Dictionary mapping role to Person
        self.add_serializable_fields(["name", "members", "roles"])


def main():
    """Run the advanced usage example."""
    print("=== Serilux Advanced Usage Example ===\n")

    # Create nested objects
    print("1. Creating nested objects...")
    person = Person()
    person.name = "Alice"
    person.age = 30

    address = Address()
    address.street = "123 Main St"
    address.city = "New York"
    address.state = "NY"
    address.zip_code = "10001"
    person.address = address

    print(f"   Person: {person.name}, Age: {person.age}")
    print(f"   Address: {person.address.street}, {person.address.city}\n")

    # Create a team with lists and dictionaries
    print("2. Creating team with lists and dictionaries...")
    team = Team()
    team.name = "Engineering"

    # Add members to list
    person1 = Person()
    person1.name = "Alice"
    person1.age = 30

    person2 = Person()
    person2.name = "Bob"
    person2.age = 25

    person3 = Person()
    person3.name = "Charlie"
    person3.age = 35

    team.members = [person1, person2, person3]

    # Add members to dictionary
    team.roles = {
        "lead": person1,
        "developer": person2,
        "senior": person3,
    }

    print(f"   Team: {team.name}")
    print(f"   Members: {[p.name for p in team.members]}")
    print(f"   Roles: {list(team.roles.keys())}\n")

    # Validate before serialization
    print("3. Validating object tree...")
    try:
        validate_serializable_tree(team)
        print("   ✓ Validation passed\n")
    except TypeError as e:
        print(f"   ✗ Validation failed: {e}\n")
        return

    # Serialize
    print("4. Serializing...")
    data = team.serialize()
    print(f"   Serialized data keys: {list(data.keys())}\n")

    # Deserialize
    print("5. Deserializing...")
    new_team = Team()
    new_team.deserialize(data)

    print(f"   Team: {new_team.name}")
    print(f"   Members: {[p.name for p in new_team.members]}")
    print(f"   Roles: {list(new_team.roles.keys())}\n")

    # Verify
    assert team.name == new_team.name
    assert len(team.members) == len(new_team.members)
    assert len(team.roles) == len(new_team.roles)
    print("✓ Advanced serialization and deserialization successful!")


if __name__ == "__main__":
    main()
