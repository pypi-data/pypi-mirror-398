PyGEAI Debugger
===============

Overview
--------

``geai-dbg`` is a command-line debugger for the ``geai`` CLI tool, part of the ``pygeai`` package. It allows developers to pause execution at specified points (breakpoints) in the ``geai`` codebase, inspect local variables, execute arbitrary Python code in the current context, and control program flow interactively. Breakpoints can be set by module or function name, providing flexibility for debugging complex CLI workflows.

The debugger is invoked by running the ``geai-dbg`` command, typically with the same arguments as the ``geai`` CLI. It pauses execution at predefined or user-specified breakpoints, presenting an interactive prompt ``(geai-dbg)`` for issuing commands.

Installation and Setup
---------------------

``geai-dbg`` is included in the ``pygeai`` package. Ensure ``pygeai`` is installed in your Python environment:

.. code-block:: bash

    pip install pygeai

No additional setup is required. The debugger script (``debugger.py``) is located in the ``pygeai.dbg`` module and can be invoked via the ``geai-dbg`` command.

Usage
-----

To use ``geai-dbg``, run it with the same arguments you would pass to the ``geai`` CLI. For example:

.. code-block:: bash

    geai-dbg ail lrs

This command runs the ``geai`` CLI with the arguments ``ail lrs`` under the debugger. The debugger automatically sets a breakpoint at the ``main`` function in the ``pygeai.cli.geai`` module, pausing execution before the ``geai`` command processes the arguments.

Upon hitting a breakpoint, the debugger displays:

- The location (module and function) where execution is paused.
- Local variables in the current context.
- An interactive prompt ``(geai-dbg)`` for entering commands.

You can then inspect variables, add breakpoints, execute code, or control execution using the available commands.

Commands
--------

At the ``(geai-dbg)`` prompt, the following commands are available:

continue, c
    Resume execution until the next breakpoint is hit or the program completes.

quit, q, Ctrl+D
    Exit the debugger, terminating the program with a clean exit status (0).

run, r
    Run the program to completion, disabling all breakpoints and skipping further pauses.

breakpoint-module, bm
    Add a breakpoint for a specific module. Prompts for a module name (e.g., ``pygeai.cli.commands``). Press Enter to set a wildcard breakpoint (any module).

breakpoint-function, bf
    Add a breakpoint for a specific function, optionally scoped to a module. Prompts for a function name (e.g., ``main``) and an optional module name. Press Enter for wildcards (any function or module).

list-modules, lm
    List all loaded modules starting with ``pygeai``, useful for identifying valid module names for breakpoints.

help, h
    Display a list of available commands and their descriptions.

<Python code>
    Execute arbitrary Python code in the current context. For example, ``print(sys.argv)`` displays the command-line arguments. Errors are caught and logged without crashing the debugger.

Ctrl+C
    Interrupt the current command input and resume execution, equivalent to ``continue``.

Examples
--------

**Example 1: Debugging a geai Command**

Suppose you want to debug the ``geai ail lrs`` command to inspect its execution. Run:

.. code-block:: bash

    geai-dbg ail lrs

Output:

.. code-block:: text

    2025-05-12 15:04:57,263 - geai - INFO - GEAI debugger started.
    2025-05-12 15:04:57,263 - geai - INFO - geai module: pygeai.cli.geai
    2025-05-12 15:04:57,263 - geai - INFO - Breakpoint added: pygeai.cli.geai:main
    2025-05-12 15:04:57,264 - geai - INFO - Setting trace and running geai
    2025-05-12 15:04:57,264 - geai - INFO - Breakpoint hit at pygeai.cli.geai.main
    2025-05-12 15:04:57,264 - geai - INFO - Local variables: {}

    Paused at pygeai.cli.geai.main
    Enter commands to execute in the current context (type 'continue' to resume, 'quit' to exit, 'help' to display available commands):
    (geai-dbg)

List available commands:

.. code-block:: text

    (geai-dbg) h
    Available commands:
      continue, c: Resume execution until next breakpoint
      quit, q: Exit the debugger
      run, r: Run program without further pauses
      breakpoint-module, bm: Add a module breakpoint
      breakpoint-function, bf: Add a function breakpoint
      list-modules, lm: List available modules
      <Python code>: Execute arbitrary Python code in the current context

List modules to find valid breakpoint targets:

.. code-block:: text

    (geai-dbg) lm
    2025-05-12 15:05:03,595 - geai - INFO - Listing available modules
    Available modules: ['pygeai', 'pygeai.dbg', 'pygeai.cli', ...]

Continue to the next breakpoint (e.g., another hit on ``main`` in a different context):

.. code-block:: text

    (geai-dbg) c
    2025-05-12 15:05:18,424 - geai - DEBUG - Alias: default
    2025-05-12 15:05:18,424 - geai - DEBUG - Base URL: api.beta.saia.ai/
    2025-05-12 15:05:18,425 - geai - INFO - Breakpoint hit at pygeai.cli.geai.main
    2025-05-12 15:05:18,425 - geai - INFO - Local variables: {'self': <pygeai.cli.geai.CLIDriver object at 0x100f34080>, 'args': None}

    Paused at pygeai.cli.geai.main
    Enter commands to execute in the current context (type 'continue' to resume, 'quit' to exit, 'help' to display available commands):
    (geai-dbg)

Run the program to completion:

.. code-block:: text

    (geai-dbg) run
    2025-05-12 15:05:21,221 - geai - INFO - Running program without further pauses.
    2025-05-12 15:05:21,222 - geai - DEBUG - Running geai with: /path/to/venv/bin/geai-dbg ail lrs
    2025-05-12 15:05:21,222 - geai - DEBUG - Listing reasoning strategies
    [geai output listing reasoning strategies]
    2025-05-12 15:05:21,878 - geai - INFO - Cleaning up trace

**Example 2: Inspecting Variables**

At a breakpoint, inspect command-line arguments:

.. code-block:: text

    (geai-dbg) print(sys.argv)
    2025-05-12 15:05:21,300 - geai - INFO - Executing interactive command: print(sys.argv)
    ['/path/to/venv/bin/geai-dbg', 'ail', 'lrs']

**Example 3: Adding a Breakpoint**

Add a breakpoint for the ``pygeai.cli.commands`` module:

.. code-block:: text

    (geai-dbg) bm
    2025-05-12 15:05:21,400 - geai - INFO - Adding breakpoint on module
    (geai-dbg) Enter module name (or press Enter for any module): pygeai.cli.commands
    2025-05-12 15:05:21,500 - geai - INFO - Breakpoint added: pygeai.cli.commands:*

Notes
-----

- **Ctrl+D and Ctrl+C**:
  - Pressing ``Ctrl+D`` at the ``(geai-dbg)`` prompt terminates the debugger gracefully, logging "Debugger terminated by user (EOF)." and exiting with status 0.
  - Pressing ``Ctrl+C`` resumes execution, equivalent to the ``continue`` command.

- **Python Code Execution**:
  - Arbitrary Python code executed at the prompt runs in the context of the paused frame, with access to local and global variables. Use with caution, as it can modify program state.

- **Breakpoint Wildcards**:
  - Use ``bm`` or ``bf`` with empty inputs to set wildcard breakpoints, pausing on any module or function. This is useful for exploratory debugging.

- **Logging**:
  - The debugger logs to stdout with timestamps, including breakpoint hits, local variables, and command execution. Errors in Python code execution are logged without crashing the debugger.

For issues or feature requests, contact the ``pygeai`` development team.

.. seealso::

   - ``geai`` CLI documentation for details on the underlying command-line tool.
   - Python's ``sys.settrace`` documentation for technical details on the debugging mechanism.