Getting started
===============

Installation
------------

Install with pip (from your internal index, Git repo, or editable install):

.. code-block:: bash

   pip install assistant-stream-ce

If you're working on the codebase locally:

.. code-block:: bash

   pip install -e .

Core concepts
-------------

assistant-stream-ce produces a stream of *chunks* (small typed events) that your client can render.

Common chunk types include:

* ``text-delta`` — incremental assistant text
* ``reasoning-delta`` — incremental reasoning text (if you choose to emit it)
* ``tool-call-begin`` / ``tool-call-delta`` / ``tool-result`` — tool call streaming
* ``update-state`` — batched state operations for client-side state syncing
* ``source`` — attach citations / sources to outputs
* ``data`` / ``error`` — arbitrary events and error reporting

The easiest way to produce a stream is :func:`assistant_stream_ce.create_run.create_run`.

A first stream
--------------

.. code-block:: python

   from assistant_stream import create_run

   async def my_run(controller):
       controller.append_text("Hello from a stream!")

   stream = create_run(my_run)

``stream`` is an async generator of chunk objects. To send it over HTTP you typically wrap it in one
of the provided Starlette responses — see :doc:`fastapi` and :doc:`streaming-formats`.

State updates
-------------

You can optionally manage a JSON-like state object that is kept locally and emitted to the client
as incremental operations (``update-state`` chunks):

.. code-block:: python

   from assistant_stream_ce import create_run

   async def run(controller):
       # initialize state
       controller.state = {"messages": "", "count": 0}

       controller.state["messages"] += "Hello"
       controller.state["count"] = controller.state["count"] + 1

   stream = create_run(run, state={})

Tool calls
----------

assistant-stream can stream tool calls with incremental arguments and a final result:

.. code-block:: python

   import json
   from assistant_stream_ce import create_run

   async def run(controller):
       tool = await controller.add_tool_call("search")
       tool.append_args_text(json.dumps({"q": "fastapi streaming"}))
       tool.set_response({"results": ["..."]})

   stream = create_run(run)

Read :doc:`tool-calls` for details and patterns.

