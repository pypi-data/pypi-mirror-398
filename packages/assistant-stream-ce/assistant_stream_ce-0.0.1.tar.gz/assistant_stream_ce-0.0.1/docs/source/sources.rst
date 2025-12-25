Sources (citations)
===================

You can attach sources to a run so the client can render citations or a "Sources" panel.

Emit a source
-------------

.. code-block:: python

   async def run(controller):
       controller.append_text("Here is the answer.")
       controller.add_source(
           id="example",
           url="https://example.com",
           title="Example Source",
       )

Sources are emitted as ``source`` chunks with fields:

* ``id`` — stable identifier you choose
* ``url`` — source URL
* ``title`` — optional display name
* ``parent_id`` — optional grouping identifier (see :doc:`tool-calls`)

