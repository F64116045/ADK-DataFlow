from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools import FunctionTool
from google.adk.tools import agent_tool
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from typing import Any, Optional
from google.adk.tools import ToolContext
import re

RED = "\033[91m"
RESET = "\033[0m"
# 連線到 Q-LLM 的 A2A
qllm_remote = RemoteA2aAgent(
    name="qllm_remote",
    description="Remote general-purpose Q-LLM agent.",
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)
qllm_tool = agent_tool.AgentTool(agent=qllm_remote)

def get_weather_report(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Returns:
        dict: A dictionary containing the weather information with a 'status' key ('success' or 'error') and a 'report' key with the weather details if successful, or an 'error_message' if an error occurred.
    """
    if city.lower() == "london":
        return {"status": "success", "report": "The current weather in London is cloudy with a temperature of 18 degrees Celsius and a chance of rain."}
    elif city.lower() == "paris":
        return {"status": "success", "report": "The weather in Paris is sunny with a temperature of 25 degrees Celsius."}
    else:
        return {"status": "error", "error_message": f"Weather information for '{city}' is not available."}

weather_tool = FunctionTool(func=get_weather_report)

def post_alert(temp: float):
    print(f"[Alert!] High temperature detected: {temp}C")

alert_tool = FunctionTool(func=post_alert)



def validate_post_alert_params(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext
) -> Optional[dict]:
    #print(f"[Policy] Validating {tool.name}, args={args}")
    if tool.name == "post_alert":
        
        temperature = args.get("temp")
        match = re.search(r"[-+]?\d*\.?\d+", temperature)
        if match:
            temperature = float(match.group())
        else:
            raise ValueError(f"Invalid temperature value: {temperature}")

        print(f"{RED}Security Policy 檢查溫度 : {RESET} {temperature} ")
        if temperature > 30000:  
            print(f"違反Policy {temperature}")
        
        return None


planner_agent = Agent(
    model="gemini-2.5-flash-lite",
    name="planner_agent",
    description="Planner agent that delegates reasoning to Q-LLM.",
    instruction=(
        "你是任務規劃代理（Planner-LLM，簡稱 P-LLM）。\n"
        "你的職責：\n"
        "1. 與使用者對話，理解並拆解需求。\n"
        "2. 規劃完整的解決步驟，直到完成任務。你不能在中途就結束，必須確保任務鏈完成並輸出結果。\n"
        "3. 呼叫工具時，直接傳入 JSON 格式的參數。\n"
        "4. 當需要 Q-LLM 解析或抽取資料時，你必須呼叫 qllm_remote，並且 **務必將請求包裝成一個乾淨的 JSON 物件**。\n"
        "   - JSON 至少包含：\n"
        "     - `request`: 自然語言的任務描述。\n"
        "     - `source`: 前面工具或結果的 key（不要展開 key，保持原樣）。\n"
        "     - （必填）`format`: 一個 JSON 範例，描述期望 Q-LLM 回傳的結構、欄位名稱與型別（型別必須是 int/float/string/bool/object/array 之一）。\n"
        "5. Q-LLM 回傳後，系統會將結果替換成新的 key。你必須保持 key 不變，直到最後輸出。\n"
        "6. 你最終輸出給使用者的內容必須是人類可讀的自然語言，但欄位值只能以 key 代替，不能自行展開。例如：\n"
        "   「巴黎的天氣是 key:xxxx，氣溫 key:yyyy 度，降雨機率 key:zzzz。」\n"
        "   真值會由系統在最後一步自動替換。\n"
        "\n"
        "⚠️ 注意：\n"
        "- 你不能直接使用工具輸出的真值，只能引用對應的 key。\n"
        "- 不要混合自然語言和 JSON 在同一個輸出中，傳給 qllm_remote 的請求必須是乾淨的 JSON。\n"
        "- format 必須包含欄位型別。\n"
        "- 不允許在取得 tool_response 後直接結束，必須完成任務鏈直到產生最終回覆。\n"
        "\n"
        "==== 範例 1：單一欄位 ====\n"
        "使用者輸入：「倫敦的溫度是多少？」\n"
        "1. 呼叫 get_weather_report：{\"city\": \"London\"}\n"
        "   → 得到 {\"status\": \"success\", \"report\": \"key:xxxx\"}\n"
        "2. 呼叫 qllm_remote：\n"
        "{\n"
        "  \"request\": \"從這份天氣報告中抽取溫度，並回傳 JSON 格式。\",\n"
        "  \"source\": \"key:xxxx\",\n"
        "  \"format\": {\"temperature\": \"float\"}\n"
        "}\n"
        "   → 得到 {\"temperature\": \"key:yyyy\"}\n"
        "3. 最後輸出給使用者：「倫敦的氣溫是 key:yyyy 度。」\n"
        "\n"
        "==== 範例 2：多個欄位 ====\n"
        "使用者輸入：「請幫我整理巴黎的天氣，告訴我溫度、天氣狀況和降雨機率。」\n"
        "1. 呼叫 get_weather_report：{\"city\": \"Paris\"}\n"
        "   → 得到 {\"status\": \"success\", \"report\": \"key:aaaa\"}\n"
        "2. 呼叫 qllm_remote：\n"
        "{\n"
        "  \"request\": \"從這份天氣報告中抽取三個欄位：溫度、天氣狀況、降雨機率，並以 JSON 格式回傳。\",\n"
        "  \"source\": \"key:aaaa\",\n"
        "  \"format\": {\n"
        "    \"temperature\": \"float\",\n"
        "    \"condition\": \"string\",\n"
        "    \"rain_chance\": \"string\"\n"
        "  }\n"
        "}\n"
        "   → 得到 {\"temperature\": \"key:bbbb\", \"condition\": \"key:cccc\", \"rain_chance\": \"key:dddd\"}\n"
        "3. 最後輸出給使用者：「巴黎的天氣是 key:cccc，氣溫 key:bbbb 度，降雨機率 key:dddd。」\n"
    ),
    tools=[weather_tool, qllm_tool, alert_tool]#,
    #before_tool_callback=validate_post_alert_params
)

       # "You are a planner agent. "
       # "When the user asks to summarize, translate, or reason about text, "
       # "you should delegate to qllm_remote by passing the text (as handle)."