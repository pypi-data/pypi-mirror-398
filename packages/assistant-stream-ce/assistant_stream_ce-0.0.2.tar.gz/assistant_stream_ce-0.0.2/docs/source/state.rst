State management
================

If you pass an initial ``state`` to :func:`assistant_stream_ce.create_run.create_run`, the controller exposes
a convenient proxy at :attr:`assistant_stream_ce.create_run.RunController.state`.

This proxy:

* lets you read values from the current state
* emits batched operations to clients (``update-state`` chunks)
* keeps a local copy of the state updated as you apply operations

Initialize state
----------------

You can set the whole state object:

.. code-block:: python

   async def run(controller):
       controller.state = {"messages": [], "draft": ""}

Or pass it to :func:`assistant_stream_ce.create_run.create_run`:

.. code-block:: python

   stream = create_run(run, state={"messages": [], "draft": ""})

Common operations
-----------------

Set a value:

.. code-block:: python

   controller.state["draft"] = "Hello"

Append text:

.. code-block:: python

   controller.state["draft"] += " world"

List append:

.. code-block:: python

   controller.state["messages"].append({"role": "assistant", "content": "Hi"})

Batching
--------

Internally, state operations are batched and flushed on the event loop tick. Before sending any other
chunk (text/tool/source/etc.), the controller flushes pending state operations to keep ordering intuitive.

Caveats
-------

* Paths must already exist for nested dictionary updates (except for setting root state).
* If you created the stream without a state (``state=None``), then ``controller.state`` is ``None``.
