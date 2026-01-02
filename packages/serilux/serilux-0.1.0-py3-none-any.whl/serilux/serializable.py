from typing import Any, Dict, List, Optional
import inspect


class SerializableRegistry:
    """Registry for serializable classes to facilitate class lookup and instantiation."""

    registry = {}

    @classmethod
    def register_class(cls, class_name: str, class_ref: type):
        """Register a class for serialization purposes by adding it to the registry.

        Args:
            class_name: The name of the class to register.
            class_ref: A reference to the class being registered.
        """
        cls.registry[class_name] = class_ref

    @classmethod
    def get_class(cls, class_name: str):
        """Retrieve a class reference from the registry by its name.

        Args:
            class_name: The name of the class to retrieve.

        Returns:
            The class reference if found, None otherwise.
        """
        return cls.registry.get(class_name)


def check_serializable_constructability(obj: "Serializable") -> None:
    """Check if a Serializable object can be constructed without arguments.

    This function validates that the object's class can be instantiated
    without arguments, which is required for proper deserialization.

    Args:
        obj: Serializable object to check.

    Raises:
        TypeError: If the object's class cannot be initialized without arguments.
            This includes detailed information about which class failed and
            what parameters are required.
    """
    obj_class = type(obj)
    init_signature = inspect.signature(obj_class.__init__)
    parameters = init_signature.parameters.values()

    required_params = []
    for param in parameters:
        if (
            param.name != "self"
            and param.default == inspect.Parameter.empty
            and param.kind != inspect.Parameter.VAR_KEYWORD
            and param.kind != inspect.Parameter.VAR_POSITIONAL
        ):
            required_params.append(param.name)

    if required_params:
        error_message = (
            f"Serialization Error: {obj_class.__name__} cannot be deserialized because "
            f"its __init__ method requires parameters: {', '.join(required_params)}\n"
            f"Serializable classes must support initialization with no arguments.\n"
            f"For Serializable subclasses, use configuration dictionary instead of constructor parameters.\n"
            f"Example:\n"
            f"  # ❌ Wrong:\n"
            f"  class MyClass(Serializable):\n"
            f"      def __init__(self, param1, param2):\n"
            f"          super().__init__()\n"
            f"          self.param1 = param1\n"
            f"\n"
            f"  # ✅ Correct:\n"
            f"  class MyClass(Serializable):\n"
            f"      def __init__(self):\n"
            f"          super().__init__()\n"
            f"          # Set config after creation:\n"
            f"          # obj.set_config(param1=value1, param2=value2)"
        )
        raise TypeError(error_message)


def validate_serializable_tree(obj: "Serializable", visited: Optional[set] = None) -> None:
    """Recursively validate that all Serializable objects in a tree can be constructed.

    This function traverses all Serializable objects referenced by the given object
    and checks that each one can be instantiated without arguments. This is useful
    for validating a Serializable object tree before serialization to catch issues early.

    Args:
        obj: Root Serializable object to validate.
        visited: Set of object IDs already visited (to avoid infinite loops).

    Raises:
        TypeError: If any Serializable object in the tree cannot be constructed
            without arguments. The error message includes the path to the problematic
            object.
    """
    if visited is None:
        visited = set()

    # Use object ID to track visited objects (avoid infinite loops)
    obj_id = id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)

    # Check the object itself
    try:
        check_serializable_constructability(obj)
    except TypeError as e:
        # Enhance error message with object information
        obj_class = type(obj).__name__
        obj_repr = repr(obj) if hasattr(obj, "__repr__") else f"{obj_class} instance"
        raise TypeError(
            f"Found non-constructable Serializable object: {obj_repr}\n" f"{str(e)}"
        ) from e

    # Recursively check all Serializable fields
    if hasattr(obj, "fields_to_serialize"):
        for field_name in obj.fields_to_serialize:
            try:
                field_value = getattr(obj, field_name, None)
            except AttributeError:
                continue

            # Import Serializable here to avoid circular import
            from serilux.serializable import Serializable as SerializableClass

            if isinstance(field_value, SerializableClass):
                try:
                    validate_serializable_tree(field_value, visited)
                except TypeError as e:
                    raise TypeError(
                        f"In field '{field_name}' of {type(obj).__name__}: {str(e)}"
                    ) from e
            elif isinstance(field_value, list):
                for i, item in enumerate(field_value):
                    if isinstance(item, SerializableClass):
                        try:
                            validate_serializable_tree(item, visited)
                        except TypeError as e:
                            raise TypeError(
                                f"In field '{field_name}[{i}]' of {type(obj).__name__}: {str(e)}"
                            ) from e
            elif isinstance(field_value, dict):
                for key, value in field_value.items():
                    if isinstance(value, SerializableClass):
                        try:
                            validate_serializable_tree(value, visited)
                        except TypeError as e:
                            raise TypeError(
                                f"In field '{field_name}[\"{key}\"]' of {type(obj).__name__}: {str(e)}"
                            ) from e


def register_serializable(cls):
    """Decorator to register a class as serializable in the registry.

    This decorator ensures that the class can be instantiated without arguments,
    which is required for proper deserialization. It validates that __init__
    either accepts no parameters (except self) or all parameters have default values.

    Args:
        cls: Class to be registered.

    Returns:
        The same class with registration completed.

    Raises:
        TypeError: If the class cannot be initialized without arguments.
            This happens when __init__ has required parameters (without defaults)
            other than 'self'. For Serializable subclasses, use configuration
            dictionary instead of constructor parameters.

    Note:
        For Serializable subclasses, all configuration should be stored in
        configuration attributes and set after object creation, not passed as
        constructor parameters. This ensures proper serialization/deserialization support.
    """
    init_signature = inspect.signature(cls.__init__)
    parameters = init_signature.parameters.values()

    for param in parameters:
        if (
            param.name != "self"
            and param.default == inspect.Parameter.empty
            and param.kind != inspect.Parameter.VAR_KEYWORD
            and param.kind != inspect.Parameter.VAR_POSITIONAL
        ):
            error_message = (
                f"Error: {cls.__name__} cannot be initialized without parameters. "
                f"Serializable classes must support initialization with no arguments.\n"
                f"For Serializable subclasses, use configuration attributes instead of constructor parameters.\n"
                f"Example: obj.config['key'] = value or set attributes after creation"
            )
            print(error_message)
            raise TypeError(error_message)
    SerializableRegistry.register_class(cls.__name__, cls)
    return cls


class Serializable:
    """A base class for objects that can be serialized and deserialized."""

    def __init__(self) -> None:
        """Initialize a serializable object with no specific fields."""
        self.fields_to_serialize = []

    def add_serializable_fields(self, fields: List[str]) -> None:
        """Add field names to the list that should be included in serialization.

        Args:
            fields: List of field names to be serialized.

        Raises:
            ValueError: If any provided field is not a string.
        """
        if not all(isinstance(field, str) for field in fields):
            raise ValueError("All fields must be strings")
        self.fields_to_serialize.extend(fields)
        self.fields_to_serialize = list(set(self.fields_to_serialize))

    def remove_serializable_fields(self, fields: List[str]) -> None:
        """Remove field names from the list that should be included in serialization.

        Args:
            fields: List of field names to be removed.
        """
        self.fields_to_serialize = [x for x in self.fields_to_serialize if x not in fields]

    def serialize(self) -> Dict[str, Any]:
        """Serialize the object to a dictionary.

        Returns:
            Dictionary containing all serializable fields.
        """
        data = {"_type": type(self).__name__}
        for field in self.fields_to_serialize:
            value = getattr(self, field, None)
            if isinstance(value, Serializable):
                data[field] = value.serialize()
            elif isinstance(value, list):
                data[field] = [
                    item.serialize() if isinstance(item, Serializable) else item for item in value
                ]
            elif isinstance(value, dict):
                data[field] = {
                    k: v.serialize() if isinstance(v, Serializable) else v for k, v in value.items()
                }
            else:
                data[field] = value
        return data

    def deserialize(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Deserialize the object from a dictionary, restoring its state.

        Args:
            data: Dictionary containing all serializable fields.
            strict: If True, raise error for unknown fields. If False, ignore them (default).

        Raises:
            ValueError: If strict=True and unknown field is found, or if deserialization fails.
        """
        unknown_fields = []
        for key, value in data.items():
            if key == "_type":
                continue

            # Validate field is in fields_to_serialize (security: prevent setting arbitrary attributes)
            if key not in self.fields_to_serialize:
                if strict:
                    unknown_fields.append(key)
                else:
                    # Silently ignore unknown fields for backward compatibility
                    continue

            try:
                if isinstance(value, dict):
                    if "_type" in value:
                        attr_class = SerializableRegistry.get_class(value["_type"])
                        if attr_class:
                            attr: Serializable = attr_class()
                            attr.deserialize(value)
                        else:
                            attr = {k: Serializable.deserialize_item(v) for k, v in value.items()}
                    else:
                        attr = {k: Serializable.deserialize_item(v) for k, v in value.items()}
                elif isinstance(value, list):
                    attr = [Serializable.deserialize_item(item) for item in value]
                else:
                    attr = value
                setattr(self, key, attr)
            except Exception as e:
                raise ValueError(
                    f"Failed to deserialize field '{key}' of {type(self).__name__}: {str(e)}"
                ) from e

        if unknown_fields and strict:
            raise ValueError(
                f"Unknown fields in {type(self).__name__}: {', '.join(unknown_fields)}. "
                f"Expected fields: {', '.join(self.fields_to_serialize)}"
            )

    @staticmethod
    def deserialize_item(item: Any) -> Any:
        """Deserialize an item (dict, list, or primitive type).

        Args:
            item: Item to deserialize (can be dict, list, or primitive type).

        Returns:
            Deserialized item.
        """
        if isinstance(item, dict):
            if "_type" in item:
                attr_class = SerializableRegistry.get_class(item["_type"])
                if not attr_class:
                    return {k: Serializable.deserialize_item(v) for k, v in item.items()}
                else:
                    obj: Serializable = attr_class()
                    obj.deserialize(item)
                    return obj
            else:
                return {k: Serializable.deserialize_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            # Fixed: variable name conflict (was: for item in item)
            return [Serializable.deserialize_item(sub_item) for sub_item in item]
        else:
            return item
