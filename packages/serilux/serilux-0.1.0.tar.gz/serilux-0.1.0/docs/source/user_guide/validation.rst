Validation
==========

Serilux provides validation functions to ensure objects can be properly deserialized.

Checking Constructability
-------------------------

Check if a single object can be constructed without arguments:

.. code-block:: python

   from serilux import check_serializable_constructability

   try:
       check_serializable_constructability(obj)
   except TypeError as e:
       print(f"Object cannot be constructed: {e}")

Validating Object Trees
-----------------------

Validate an entire tree of Serializable objects:

.. code-block:: python

   from serilux import validate_serializable_tree

   try:
       validate_serializable_tree(obj)
   except TypeError as e:
       print(f"Validation failed: {e}")

This is useful before serialization to catch issues early.

