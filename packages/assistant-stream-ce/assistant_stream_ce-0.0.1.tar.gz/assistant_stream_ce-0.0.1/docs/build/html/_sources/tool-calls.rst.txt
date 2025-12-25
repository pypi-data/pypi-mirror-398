Tool calls
==========

Tool calls are useful when you want the client to display tool execution as part of the assistant run.

Streaming a tool call
---------------------

Use :meth:`assistant_stream_ce.create_run.RunController.add_tool_call` to start a tool call and get a
:class:`assistant_stream_ce.modules.tool_call.ToolCallController`:

.. code-block:: python

   import json

   async def run(controller):
       tool = await controller.add_tool_call("weather")
       tool.append_args_text(json.dumps({"location": "Athens"}))
       tool.set_response({"temp_c": 18})

The library emits:

1. ``tool-call-begin`` chunk
2. One or more ``tool-call-delta`` chunks (argument text deltas)
3. A final ``tool-result`` chunk

Tool call IDs
-------------

If you don't provide a ``tool_call_id``, assistant-stream generates one in the ``call_...`` style:

.. autofunction:: assistant_stream_ce.modules.tool_call.generate_openai_style_tool_call_id

Returning artifacts
-------------------

When sending a tool result, you may also include an ``artifact`` payload and/or set ``is_error=True``:

.. code-block:: python

   tool.set_response(
       {"ok": False, "message": "failed"},
       artifact={"debug": "..."},
       is_error=True,
   )

Nested streams
--------------

Tool calls are implemented as substreams that are merged into the parent stream. You can create more
complex behavior by combining multiple streams with :meth:`assistant_stream.create_run.RunController.add_stream`.

