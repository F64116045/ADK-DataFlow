from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from typing import Any, Optional


class PrintFlowPlugin(BasePlugin):
    """最安全的 Plugin：只用來 Debug 流程，不修改任何內容"""

    def __init__(self):
        super().__init__(name="print_flow")

    # ---------------- Agent ----------------
    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        print(f"[DEBUG] === BEFORE AGENT === agent={agent.name}")

    async def after_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ) -> None:
        print(f"[DEBUG] === AFTER AGENT === agent={agent.name}")

    # ---------------- Model ----------------
    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> None:
        print("[DEBUG] === BEFORE MODEL ===")
        print(llm_request.model_dump_json(indent=2))

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> None:
        print("[DEBUG] === AFTER MODEL ===")
        print(llm_response.model_dump_json(indent=2))

    async def on_model_error_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest, error: Exception
    ) -> None:
        print("[DEBUG] === MODEL ERROR ===")
        print(f"Error: {repr(error)}")