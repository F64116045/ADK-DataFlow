from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from .handle_manager import HandleManager
from google.adk.agents.base_agent import BaseAgent
from google.adk.tools.base_tool import BaseTool
from typing import Any, Optional
from google.adk.tools import ToolContext, FunctionTool
import re
import inspect, sys
from google.genai import types as genai_types

class KeyPlugin(BasePlugin):
    """攔截 Request/Response"""

    def __init__(self):
        super().__init__(name="handle_manager")
        self.handle_manager = HandleManager()


    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ):
        print(f"BeforeAgent: {agent.name}")
        print(f"Args: {callback_context.user_content}")

    


    #async def after_agent_callback(
    #    self,
    #    *,
    #    agent: BaseAgent,
    #    callback_context: CallbackContext,
    #) -> Optional[genai_types.Content]:
    #    if agent.name == "qllm_remote":
            #print("📝 [KeyPlugin] 攔截 Q-LLM 的輸出")

            # Agent 的輸出其實在 callback_context.state 或 user_content / events
            # 如果需要最終結果，你可以在這裡讀取並加工

            # 假設這裡把 agent 最後結果存起來
            #key = self.handle_manager.save(
                #callback_context.user_content,  # or other field depending on result
                #type_hint=f"agent:{agent.name}"
            #)
            #print(f"🗄️ 已將 Agent {agent.name} 的輸出存成 key:{key}")

            # 回傳替代結果 (Content)
            #return genai_types.Content(
                #role="model",
                #parts=[genai_types.Part.from_text(text=f"key:{key}")]
            #)


        
        #return None   # 其他 agent 保持原樣
            
    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict[str, Any],
    ) -> Optional[dict]:
        if tool.name != "qllm_remote":
            print(f"---------- 攔截到 Tool {tool.name} 的輸出")
            print(f"---------- 輸入參數: {tool_args}")
            print(f"---------- 原始輸出: {result}")

            # 把結果存進 HandleManager
            key = self.handle_manager.save(result, type_hint=f"tool:{tool.name}")
            print(f"---------- 已將 Tool {tool.name} 的輸出存成 key:{key}")

            # 回傳 mapping 後的結果（用 key 取代原始輸出）
            return {"result": f"key:{key}"}


    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict | None:
        if tool.name == "qllm_remote":
            req = tool_args.get("request", "")
            print(f"---------- Intercept before calling qllm_remote, request={req}")

            # 找出 key:xxxx pattern
            match = re.search(r"key:([A-Za-z0-9\-]+)", req)
            if match:
                key = match.group(1)
                try:
                    resolved_value = self.handle_manager.resolve(key)
                    print(f"🔓 Resolved key:{key} -> {resolved_value}")

                    # 替換掉 request 裡的 key:xxxx
                    new_req = req.replace(f"key:{key}", str(resolved_value))
                    tool_args["request"] = new_req
                except KeyError:
                    print(f"---------- Key {key} not found in HandleManager.")
            else:
                print("---------- No key pattern found in request.")

        return None  # 繼續執行原本的 tool，只是換掉參數



