FastAPI / Starlette integration
===============================

assistant-stream-ce includes small response helpers that make it easy to return a stream from a FastAPI
route.

Pick a transport
----------------

You typically choose one of these:

* :class:`assistant_stream_ce.serialization.data_stream.DataStreamResponse` — **assistant-ui data stream**
  format (plain text)
* :class:`assistant_stream_ce.serialization.assistant_transport.AssistantTransportResponse` — SSE with a JSON payload
  per event (also used by assistant-ui transports)
* :class:`assistant_stream_ce.serialization.openai_stream.OpenAIStreamResponse` — minimal OpenAI-compatible chunk stream
  (currently only streams text deltas)

Example: assistant-ui DataStreamResponse
----------------------------------------

.. code-block:: python

   from fastapi import FastAPI
   from assistant_stream_ce import create_run
   from assistant_stream_ce.serialization.data_stream import DataStreamResponse

   app = FastAPI()

   @app.get("/chat")
   async def chat():
       async def run(controller):
           controller.append_text("Hello from FastAPI!")
       return DataStreamResponse(create_run(run))

Example: SSE JSON events (AssistantTransportResponse)
-----------------------------------------------------

.. code-block:: python

   from fastapi import FastAPI
   from assistant_stream_ce import create_run
   from assistant_stream_ce.serialization.assistant_transport import AssistantTransportResponse

   app = FastAPI()

   @app.get("/chat-sse")
   async def chat_sse():
       async def run(controller):
           controller.append_text("Streaming over SSE...")
       return AssistantTransportResponse(create_run(run))

CORS and streaming
------------------

If you serve a browser client, remember to configure CORS for your API, and ensure your hosting
stack supports streaming responses without buffering.

Notes:

* For SSE (``text/event-stream``), proxies must not buffer the response.
* For the Data Stream (``text/plain``), the server should flush frequently.

Error handling
--------------

If your run callback raises, :func:`assistant_stream_ce.create_run.create_run` will emit an ``error``
chunk with the exception string and then re-raise.

A common pattern is to catch expected exceptions inside your callback and emit a user-friendly error:

.. code-block:: python

   async def run(controller):
       try:
           ...
       except ValueError as e:
           controller.add_error(f"Bad input: {e}")
           return

