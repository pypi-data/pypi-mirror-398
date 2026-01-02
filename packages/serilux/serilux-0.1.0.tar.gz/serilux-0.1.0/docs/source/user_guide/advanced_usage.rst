Advanced Usage
==============

This guide covers advanced features of Serilux.

Nested Objects
--------------

Serilux automatically handles nested Serializable objects:

.. code-block:: python

   @register_serializable
   class Address(Serializable):
       def __init__(self):
           super().__init__()
           self.street = ""
           self.city = ""
           self.add_serializable_fields(["street", "city"])

   @register_serializable
   class Person(Serializable):
       def __init__(self):
           super().__init__()
           self.name = ""
           self.address = None
           self.add_serializable_fields(["name", "address"])

Lists and Dictionaries
----------------------

Serilux handles lists and dictionaries containing Serializable objects:

.. code-block:: python

   @register_serializable
   class Team(Serializable):
       def __init__(self):
           super().__init__()
           self.name = ""
           self.members = []
           self.add_serializable_fields(["name", "members"])

   team = Team()
   team.name = "Engineering"
   team.members = [person1, person2, person3]

   data = team.serialize()

Using the Registry
------------------

You can manually register classes:

.. code-block:: python

   from serilux import SerializableRegistry

   SerializableRegistry.register_class("MyClass", MyClass)

   # Retrieve a class
   cls = SerializableRegistry.get_class("MyClass")

