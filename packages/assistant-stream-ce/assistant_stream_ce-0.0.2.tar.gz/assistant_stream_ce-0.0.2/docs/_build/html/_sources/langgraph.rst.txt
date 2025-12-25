LangGraph integration
=====================

If you use **LangGraph** / **LangChain**, assistant-stream provides helpers for:

* appending LangGraph events into a state object
* extracting/initializing tool subgraph state for streamed tool execution

These helpers are available only if the LangGraph/LangChain dependencies are installed.

Append LangGraph events
-----------------------

.. autofunction:: assistant_stream_ce.modules.langgraph.append_langgraph_event

Tool subgraph state helper
--------------------------

.. autofunction:: assistant_stream_ce.modules.langgraph.get_tool_call_subgraph_state

Typical usage
-------------

.. code-block:: python

   from assistant_stream_ce import create_run
   from assistant_stream_ce.modules.langgraph import append_langgraph_event

   async def run(controller):
       # Ensure state has a place for messages
       controller.state = {"messages": []}

       # In your LangGraph event handler:
       append_langgraph_event(controller.state, "ns", "messages", payload=[...])

