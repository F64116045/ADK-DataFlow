from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools import FunctionTool
from google.adk.tools import agent_tool
from google.adk.agents import LlmAgent

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

planner_agent = Agent(
    model="gemini-2.5-flash",
    name="planner_agent",
    description="Planner agent that delegates reasoning to Q-LLM.",
    instruction=(
        "你是主要規劃任務的 LLM\n"
        "你要做的事：\n"
        "1. 與 User 對話，理解並拆解任務需求。\n"
        "2. 規劃任務步驟，並決定哪些需要呼叫工具或 Q-LLM。\n"
        "3. 當需要解析原始資料時如工具回傳值，組裝你需要的欄位的格式，交給 Q-LLM，明確告知你需要甚麼。\n"
        "4. 你必須要指定 Q-LLM 回傳的 JSON 格式，並附帶key，請嚴格遵守以下格式: {[指令與你要的JSON資料]，[key=xxxxx]}\n"
        "5. Q-LLM 回傳的結果也是一個 key ，你就當作那個 Key 是答案，並把Key放進你的回答中回傳給 User。\n"
    ),
    tools = [weather_tool, qllm_tool]
)
       # "You are a planner agent. "
       # "When the user asks to summarize, translate, or reason about text, "
       # "you should delegate to qllm_remote by passing the text (as handle)."