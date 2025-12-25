import unittest
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from assistant_stream_ce.modules.langgraph import append_langgraph_event, get_tool_call_subgraph_state

class MockRunController:
    def __init__(self, state=None):
        self.state = state if state is not None else {}

class TestLangGraph(unittest.TestCase):

    ## --- Tests for append_langgraph_event ---

    def test_append_new_human_message(self):
        state = {"messages": []}
        # Note: implementation uses "messages", not "message"
        msg = HumanMessage(content="Hello", id="1")
        append_langgraph_event(state, "ns", "messages", [msg])
        
        self.assertEqual(len(state["messages"]), 1)
        self.assertEqual(state["messages"][0]["content"], "Hello")
        self.assertEqual(state["messages"][0]["type"], "human")

    def test_merge_ai_chunks(self):
        # Implementation uses ._get_value() which assumes a specific object structure
        # Here we mock the behavior expected by add_ai_message_chunks
        state = {
            "messages": [
                {"type": "ai", "content": "Hello", "id": "chunk_1"}
            ]
        }
        # In actual use, state messages should be compatible with AIMessageChunk params
        chunk = AIMessageChunk(content=" World", id="chunk_1")
        
        # We need to monkeypatch the dict to have _get_value for your specific implementation
        class MockMsgDict(dict):
            def _get_value(self): return self

        state["messages"][0] = MockMsgDict(state["messages"][0])
        
        append_langgraph_event(state, "ns", "messages", [chunk])
        self.assertEqual(state["messages"][0]["content"], "Hello World")

    def test_updates_event_logic(self):
        state = {}
        payload = {
            "node_a": {"user_id": 123, "messages": "ignored"},
            "node_b": {"score": 0.95}
        }
        append_langgraph_event(state, "ns", "updates", payload)
        
        self.assertEqual(state["user_id"], 123)
        self.assertEqual(state["score"], 0.95)
        self.assertNotIn("messages", state)

    ## --- Tests for get_tool_call_subgraph_state ---

    def test_get_tool_call_subgraph_state_creation(self):
        # Setup state with an AI message waiting for a tool response
        initial_state = {
            "messages": [{
                "type": "ai",
                "tool_calls": [{"name": "my_tool", "id": "call_1", "args": {}}]
            }]
        }
        controller = MockRunController(initial_state)
        
        # This should trigger the creation of a ToolMessage in the state
        res = get_tool_call_subgraph_state(
            controller, 
            namespace=("sub_node:123",), 
            subgraph_node="sub_node", 
            default_state={"initialized": True},
            tool_name="my_tool"
        )
        
        # Verify the ToolMessage was appended to controller.state
        self.assertEqual(len(controller.state["messages"]), 2)
        self.assertEqual(controller.state["messages"][1]["type"], "tool")
        self.assertEqual(controller.state["messages"][1]["tool_call_id"], "call_1")
        # Verify it returned the default state as the artifact
        self.assertEqual(res, {"initialized": True})

if __name__ == "__main__":
    unittest.main()
