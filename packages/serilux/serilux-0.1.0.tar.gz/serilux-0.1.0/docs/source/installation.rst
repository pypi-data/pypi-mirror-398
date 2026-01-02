Installation
============

Quick Install
------------

The easiest way to install Serilux is using pip:

.. code-block:: bash

   pip install serilux

That's it! You're ready to go.

Development Install
-------------------

For development with all dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

Or using Makefile:

.. code-block:: bash

   make dev-install

Requirements
------------

- Python 3.7 or higher
- No external dependencies (pure Python)

Optional Dependencies
----------------------

For development:

- pytest>=7.0.0
- pytest-cov>=4.0.0
- black>=22.0.0
- flake8>=5.0.0
- mypy>=0.991

For documentation:

- sphinx>=5.0.0
- sphinx-rtd-theme>=1.0.0
- furo>=2024.1.0
- sphinx-autodoc-typehints>=1.19.0
- sphinx-copybutton>=0.5.0
- sphinx-design>=0.5.0

Verifying Installation
----------------------

You can verify that Serilux is installed correctly:

.. code-block:: python

   import serilux
   print(serilux.__version__)

Next Steps
----------

- Read the :doc:`quickstart` guide to get started
- Check out the :doc:`user_guide/index` for detailed usage

