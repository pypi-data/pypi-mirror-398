Streaming formats
=================

assistant-stream-ce separates **what you produce** (typed chunks) from **how you encode** those chunks
for HTTP streaming.

Chunk stream (source of truth)
------------------------------

Your application produces an async generator of :data:`assistant_stream_ce.assistant_stream_chunk.AssistantStreamChunk`.

Encoding options
----------------

Data stream (assistant-ui)
^^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`assistant_stream_ce.serialization.data_stream.DataStreamEncoder` converts chunks to a newline-delimited
protocol used by **assistant-ui**.

Response class:
:class:`assistant_stream_ce.serialization.data_stream.DataStreamResponse`

SSE JSON transport
^^^^^^^^^^^^^^^^^^

:class:`assistant_stream_ce.serialization.assistant_transport.AssistantTransportEncoder` converts each chunk to a JSON object
and emits it as a :sse:``Server-Sent Event`` payload.

Response class:
:class:`assistant_stream_ce.serialization.assistant_transport.AssistantTransportResponse`

OpenAI-style SSE
^^^^^^^^^^^^^^^^

:class:`assistant_stream_ce.serialization.openai_stream.OpenAIStreamEncoder` emits OpenAI-like ``chat.completion.chunk`` events.
At the moment it only maps ``text-delta`` chunks to ``delta.content``.

Response class:
:class:`assistant_stream_ce.serialization.openai_stream.OpenAIStreamResponse`

Custom encoders
---------------

To implement your own encoder, subclass :class:`assistant_stream_ce.serialization.stream_encoder.StreamEncoder`:

.. code-block:: python

   from assistant_stream_ce.serialization.stream_encoder import StreamEncoder

   class MyEncoder(StreamEncoder):
       def get_media_type(self) -> str:
           return "text/plain"

       async def encode_stream(self, stream):
           async for chunk in stream:
               yield f"{chunk.type}\n"

Then use :class:`assistant_stream_ce.serialization.assistant_stream_response.AssistantStreamResponse`:

.. code-block:: python

   from assistant_stream_ce.serialization.assistant_stream_response import AssistantStreamResponse

   return AssistantStreamResponse(create_run(run), MyEncoder())

