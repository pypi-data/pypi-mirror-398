Welcome to assistant-stream
===========================

**assistant-stream** is a small library for building *typed* assistant streaming responses in Python.
It is designed to work well with:

* **FastAPI / Starlette** responses (via :class:`assistant_stream_ce.serialization.assistant_stream_response.AssistantStreamResponse`)
* **assistant-ui** transports (via :class:`assistant_stream_ce.serialization.data_stream.DataStreamResponse`
  or :class:`assistant_stream_ce.serialization.assistant_transport.AssistantTransportResponse`)

At the core is :func:`assistant_stream_ce.create_run.create_run`, which turns an async callback into an
async generator that yields structured stream chunks.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting-started
   fastapi
   streaming-formats
   state
   tool-calls
   sources
   langgraph

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index

Quick example
-------------

A minimal FastAPI endpoint streaming assistant output:

.. code-block:: python

   from fastapi import FastAPI
   from assistant_stream_ce import create_run
   from assistant_stream_ce.serialization.data_stream import DataStreamResponse

   app = FastAPI()

   @app.get("/chat")
   async def chat():
       async def run(controller):
           controller.append_text("Hello ")
           controller.append_text("world!")

       return DataStreamResponse(create_run(run))

Next steps:

* Read :doc:`getting-started` for a tour of the features.
* See :doc:`fastapi` for practical server patterns and tips.
