Basic Usage
===========

This guide covers the basic usage of Serilux.

Creating Serializable Classes
------------------------------

To create a serializable class, inherit from ``Serializable`` and use the
``@register_serializable`` decorator:

.. code-block:: python

   from serilux import Serializable, register_serializable

   @register_serializable
   class MyClass(Serializable):
       def __init__(self):
           super().__init__()
           self.field1 = ""
           self.field2 = 0
           self.add_serializable_fields(["field1", "field2"])

Registering Fields
------------------

Use ``add_serializable_fields()`` to specify which fields should be serialized:

.. code-block:: python

   obj.add_serializable_fields(["field1", "field2", "field3"])

You can also remove fields:

.. code-block:: python

   obj.remove_serializable_fields(["field2"])

Serialization
-------------

Serialize an object to a dictionary:

.. code-block:: python

   data = obj.serialize()
   # Returns: {'_type': 'MyClass', 'field1': 'value1', 'field2': 42}

Deserialization
---------------

Deserialize from a dictionary:

.. code-block:: python

   new_obj = MyClass()
   new_obj.deserialize(data)

Strict Mode
-----------

Enable strict mode to raise errors for unknown fields:

.. code-block:: python

   obj.deserialize(data, strict=True)

