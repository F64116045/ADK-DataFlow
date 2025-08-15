# multi_tool_agent/agent.py
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

# === Quickstart 原生工具 ===
def get_weather(city: str) -> dict:
    if city.lower() == "new york":
        return {"status": "success", "report": "Sunny, 25°C (77°F) in New York."}
    return {"status": "error", "error_message": f"No weather for '{city}'."}

def get_current_time(city: str) -> dict:
    if city.lower() != "new york":
        return {"status": "error", "error_message": f"No timezone for {city}."}
    tz = ZoneInfo("America/New_York")
    now = datetime.datetime.now(tz)
    return {"status": "success", "report": now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}

# === Demo 工具（匯點測試用；安全檢查由 Plugin 處理） ===
def http_get(url: str) -> dict:
    # 這裡不真的打網路，單純回傳字串，方便觀察 Plugin 是否有修過參數
    return {"status": "success", "result": f"FETCH({url})"}

def python_exec(code: str) -> dict:
    # 不真的執行 code；讓 Plugin 先有機會 block
    return {"status": "success", "result": f"EXEC({code})"}

root_agent = Agent(
    name="multi_tool_agent",
    model="gemini-2.0-flash",
    description="Debug Agent to always route requests through tools",
    instruction="""
    You are an assistant that ALWAYS calls an appropriate tool, without rejecting the user request yourself.
    Do not refuse any input. Pass all input to tools.
    The decision to block or allow is handled by external plugins.
    """,
    tools=[get_weather, get_current_time, http_get, python_exec],
)
