State Management
================

routilux provides comprehensive state management through JobState and ExecutionTracker.

JobState
--------

JobState tracks the execution state of a flow:

.. code-block:: python

   from routilux import JobState

   job_state = JobState(flow_id="my_flow")

Status Values
-------------

JobState can have the following status values:

* ``pending`` - Initial state
* ``running`` - Currently executing
* ``paused`` - Execution paused
* ``completed`` - Execution completed successfully
* ``failed`` - Execution failed
* ``cancelled`` - Execution cancelled

Updating Routine State
----------------------

Update the state of a specific routine:

.. code-block:: python

   job_state.update_routine_state("routine1", {
       "status": "completed",
       "stats": {"count": 1},
       "result": "success"
   })

Getting Routine State
---------------------

Retrieve the state of a routine:

.. code-block:: python

   state = job_state.get_routine_state("routine1")

Recording Execution History
---------------------------

Record execution events:

.. code-block:: python

   job_state.record_execution(
       routine_id="routine1",
       event_name="output",
       data={"result": "success"}
   )

Getting Execution History
-------------------------

Retrieve execution history:

.. code-block:: python

   # Get all history
   history = job_state.get_execution_history()
   
   # Get history for a specific routine
   history = job_state.get_execution_history(routine_id="routine1")

ExecutionTracker
----------------

ExecutionTracker provides performance monitoring:

.. code-block:: python

   tracker = flow.execution_tracker

   # Get performance for a routine
   perf = tracker.get_routine_performance("routine1")
   
   # Get overall flow performance
   flow_perf = tracker.get_flow_performance()

Performance Metrics
-------------------

Performance metrics include:

* Total executions
* Success/failure counts
* Success rate
* Average execution time
* Min/max execution times

