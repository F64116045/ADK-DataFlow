from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from typing import Any, Optional


class HandleManagerPlugin(BasePlugin):
    """一個示範 Plugin：可稍微修改 model request/response，並記錄流程"""

    def __init__(self):
        super().__init__(name="handle_manager")

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
    ) -> Optional[LlmRequest]:
        print("[DEBUG] === BEFORE MODEL ===")
        print(llm_request.model_dump_json(indent=2))


        if llm_request.contents and llm_request.contents[0].parts:
            part = llm_request.contents[0].parts[0]
            if getattr(part, "text", None):
                part.text = "\n[TEST] 請翻譯：這是一個測試句子"


    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        print("[DEBUG] === AFTER MODEL ===")
        print(llm_response.model_dump_json(indent=2))

        if llm_response and llm_response.content:
            for part in llm_response.content.parts:
                if getattr(part, "text", None):
                    part.text += " [DEBUG RESPONSE]"



    async def on_model_error_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest, error: Exception
    ) -> None:
        print("[DEBUG] === MODEL ERROR ===")
        print(f"Error: {repr(error)}")

    