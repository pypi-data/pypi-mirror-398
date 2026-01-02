Design Overview
===============

Routilux is an event-driven workflow orchestration framework that provides flexible connection mechanisms, state management, and workflow orchestration capabilities.

Core Improvements
-----------------

1. **Slots and Events Mechanism**: Changed from signal mechanism to more explicit slots (input slots) and events (output events)
2. **Many-to-Many Connections**: Support for one slot connecting to multiple events, and one event connecting to multiple slots
3. **State Management**: Each routine provides a ``stats()`` method for state tracking
4. **Flow Manager**: Unified workflow orchestration, persistence, and recovery mechanism
5. **JobState Management**: Support for execution state recording and recovery (resume) functionality

Core Concepts
-------------

Routine Objects
~~~~~~~~~~~~~~~

Each Routine object is a node in the workflow with the following characteristics:

* **Slots (Input Slots)**: 0-N input slots for receiving data from other routines
* **Events (Output Events)**: 0-N output events for sending data to other routines
* **Stats (State)**: A dictionary for storing all state information during routine execution

Connection Relationships
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Routine A (Event: "result") ──┐
                                  ├──> Routine B (Slot: "input")
   Routine C (Event: "output") ──┘

   Routine D (Event: "data") ──┬──> Routine E (Slot: "input1")
                               └──> Routine F (Slot: "input2")

* **One-to-Many**: One event can connect to multiple slots
* **Many-to-One**: Multiple events can connect to the same slot (requires merge strategy)
* **Many-to-Many**: Fully flexible connection patterns

Flow
~~~~

A Flow is a directed graph consisting of multiple Routine nodes and their connections.

JobState
~~~~~~~~

JobState records the execution state of a flow, including:

* Current executing routine
* Execution state of each routine
* Passed data
* Execution history

Architecture
------------

Module Structure
~~~~~~~~~~~~~~~~

.. code-block:: text

   routilux/
   ├── __init__.py
   ├── routine.py          # Routine base class
   ├── flow.py             # Flow manager
   ├── job_state.py        # JobState management
   ├── connection.py       # Connection management
   └── serialization_utils.py  # Serialization support

Class Design
~~~~~~~~~~~~

Routine Class
^^^^^^^^^^^^^^

The improved Routine base class with:

* Support for slots (input slots)
* Support for events (output events)
* Provides ``stats()`` method returning state dictionary

Slot Class
^^^^^^^^^^

Input slot that can:

* Connect to multiple events (many-to-many relationship)
* Support data reception and processing
* Support merge strategies (override, append, custom)

Event Class
^^^^^^^^^^^

Output event that can:

* Connect to multiple slots (many-to-many relationship)
* Support event triggering and data passing
* Pass data through Connection with parameter mapping

Flow Class
^^^^^^^^^^

Flow manager responsible for:

* Managing multiple Routine nodes
* Managing connections between nodes
* Executing workflows
* Persistence and recovery

JobState Class
^^^^^^^^^^^^^^

Job state that records:

* Flow execution state
* State of each routine
* Passed data
* Execution history

Design Principles
-----------------

Separation of Concerns
~~~~~~~~~~~~~~~~~~~~~~

* **Flow (Control Layer)**: Responsible for execution control
  * ``pause()``, ``resume()``, ``cancel()`` - Execution control methods
  
* **JobState (Data Layer)**: Responsible for state storage and queries
  * State query methods
  * Internal state update methods (called by Flow)

This separation ensures clear responsibilities and avoids interface duplication.

