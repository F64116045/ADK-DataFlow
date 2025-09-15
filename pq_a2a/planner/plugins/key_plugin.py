from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from .handle_manager import HandleManager


class KeyPlugin(BasePlugin):
    """攔截 Request/Response，把敏感內容轉成 handle (LLM 永遠碰不到原始值)"""

    def __init__(self):
        super().__init__(name="handle_manager")
        self.handle_manager = HandleManager()

    # -------- Before Model  --------
    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> None:
        print("[DEBUG] === BEFORE MODEL ===")
        print(llm_request.model_dump_json(indent=2))

        for content in llm_request.contents:
            for part in content.parts:
                if part.text and len(part.text) > 20:
                    key = self.handle_manager.save(part.text, type_hint="user_text")
                    part.text = f"[HANDLE:{key}]"

    # -------- After Model  --------
    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> None:
        print("[DEBUG] === AFTER MODEL ===")
        print(llm_response.model_dump_json(indent=2))

