Changelog
=========

Version 0.1.2
-------------

Released: 2024-12-26

New Features
~~~~~~~~~~~~

* ✅ **ErrorHandler**: Error handler supporting multiple error handling strategies (stop, continue, retry, skip)
* ✅ **Error Recovery Strategies**: Support for configuring error handling strategies and retry mechanisms
* ✅ **Pause and Resume**: Flow supports pause and resume functionality
* ✅ **Cancel Functionality**: Flow supports canceling execution

Improvements
~~~~~~~~~~~~

* ✅ **Error Handling Integration**: Flow.execute integrates error handler
* ✅ **Retry Mechanism**: Supports automatic retry with configurable retry count and delay
* ✅ **Pause Point Recording**: Records pause points and checkpoint information
* ✅ **Design Optimization**: Optimized responsibility separation for pause/resume/cancel
  * Flow responsible for execution control (pause/resume/cancel)
  * JobState only responsible for state recording and queries
  * Removed public pause/resume/cancel methods from JobState, changed to internal methods

Version 0.1.1
-------------

Released: 2024-12-26

New Features
~~~~~~~~~~~~

* ✅ **ExecutionTracker**: Execution tracker that tracks flow execution state, performance, and event flow
* ✅ **Execution History Recording**: Automatically records all emitted events to JobState
* ✅ **Performance Metrics**: Supports getting routine and flow performance metrics
* ✅ **Detailed State Tracking**: Records execution time, start/end times, and other detailed information

Improvements
~~~~~~~~~~~~

* ✅ **Error Handling**: More comprehensive error recording and handling
* ✅ **Execution Time Tracking**: Automatically calculates and records execution time for each routine
* ✅ **Event Flow Tracking**: Records all event triggers and passes

Version 0.1.0
-------------

Released: 2024-01-XX

Initial release with core functionality:

New Features
~~~~~~~~~~~~

* ✅ **Routine Base Class**: Supports defining slots and events, provides stats() method
* ✅ **Slot Class**: Input slot supporting connection to multiple events, data reception and processing
* ✅ **Event Class**: Output event supporting connection to multiple slots, event triggering
* ✅ **Connection Class**: Connection object supporting parameter mapping
* ✅ **Flow Class**: Flow manager supporting workflow orchestration, execution, and recovery
* ✅ **JobState Class**: Job state management supporting state recording and persistence
* ✅ **ExecutionRecord Class**: Execution record

Improvements
~~~~~~~~~~~~

* ✅ **Event-Driven Execution**: Implemented event-driven execution mechanism
* ✅ **Parameter Mapping**: Improved Connection parameter mapping functionality
* ✅ **Intelligent Parameter Matching**: Slot.receive can now intelligently match handler parameters
* ✅ **Flow Context**: Routine.emit can automatically get Flow context

Testing
~~~~~~~

* ✅ Basic functionality tests passed
* ✅ Flow execution tests passed (linear flow, branch flow, parameter mapping)

Known Issues
~~~~~~~~~~~~

* ⚠️ Flow persistence only saves structure, not routine instances
* ⚠️ Need to improve asynchronous execution support
* ⚠️ Need to implement complete test cases

