Installation
============

Requirements
------------

* Python 3.7 or higher
* Dependencies (see below)

Installing from Source
-----------------------

Clone the repository and install:

.. code-block:: bash

   git clone <repository-url>
   cd routilux
   pip install -e .

Installing Dependencies
-----------------------

Routilux is a standalone package with no external dependencies. All required functionality is included in the package.

Development Installation
------------------------

For development, install with development dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

Verifying Installation
-----------------------

After installation, verify the installation:

.. code-block:: python

   from routilux import Flow, Routine
   print("Installation successful!")

