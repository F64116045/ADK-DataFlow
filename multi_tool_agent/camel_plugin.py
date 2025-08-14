# multi_tool_agent/camel_plugin.py
from google.adk.agents.base_agent import BaseAgent
from google.adk.tools import ToolContext
from google.adk.plugins.base_plugin import BasePlugin
from typing import Optional, Any

class CamelFlowPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="camel_flow")

    async def before_tool_callback(
        self,
        *,
        tool,                     # BaseTool 實例
        tool_args: dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[dict]:
        """
        在工具執行前攔截：
        - 讀取輸入參數
        - 做 Data Flow 標籤檢查
        - 視情況修改輸入或阻擋執行
        """
        print(f"[CamelFlowPlugin] Tool '{tool.name}' 即將執行，輸入參數: {tool_args}")

        # 紀錄到 state（跨工具可讀寫）
        tool_context.state["camel:last_tool_input"] = {
            "tool": tool.name,
            "args": tool_args
        }

        # ====== 範例：阻擋危險命令 ======
        if tool.name == "python_exec" and "rm -rf" in str(tool_args):
            print("[CamelFlowPlugin] 阻擋危險命令")
            return {"status": "error", "error_message": "Command blocked by CamelFlow policy"}

        # ====== 範例：修正惡意 URL ======
        if tool.name == "fetch" and "evil.com" in str(tool_args):
            print("[CamelFlowPlugin] 修正惡意 URL")
            tool_args["url"] = str(tool_args["url"]) + "_safe"

        # 回傳 None 表示繼續正常執行
        return None
