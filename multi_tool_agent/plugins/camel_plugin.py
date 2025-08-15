# multi_tool_agent/camel_plugin.py
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types
from typing import Optional, Any
import uuid

from .dfg import DataFlowGraph, DFNode
from .policies import is_tool_allowed

class CamelFlowPlugin(BasePlugin):
    def __init__(self):
        super().__init__(name="camel_flow")
        self.dfg = DataFlowGraph()

    async def on_user_message_callback(self, *, invocation_context, user_message):
        node_id = str(uuid.uuid4())
        value_text = " ".join([p.text for p in user_message.parts if hasattr(p, "text")])
        # 預設使用者輸入都是 untrusted
        node = DFNode(node_id=node_id, value=value_text, origin="user", capabilities=["untrusted"], taints=["untrusted"])
        self.dfg.add_node(node)
        print(f"[CamelFlowPlugin] 新增使用者輸入節點: {node.value}")
        return None

    async def before_tool_callback(self, *, tool, tool_args, tool_context):
        for arg_value in tool_args.values():
            matched_nodes = self.dfg.find_nodes_with_value(arg_value)
            for node in matched_nodes:
                if not is_tool_allowed(tool.name, node.taints):
                    return {
                        "status": "error",
                        "error_message": f"Tool '{tool.name}' 無權存取此資料: {node.value}"
                    }
        return None
    