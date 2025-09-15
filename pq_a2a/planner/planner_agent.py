from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# 連線到 Q-LLM 的 A2A
qllm_remote = RemoteA2aAgent(
    name="qllm_remote",
    description="Remote general-purpose Q-LLM agent.",
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)

planner_agent = Agent(
    model="gemini-2.5-flash",
    name="planner_agent",
    description="Planner agent that delegates reasoning to Q-LLM.",
    instruction=(
        "你是主要規劃任務的 LLM\n"
        "你要做的事：\n"
        "1. 與 User 對話，理解並拆解任務需求。\n"
        "2. 規劃任務步驟，並決定哪些需要呼叫工具或 Q-LLM。\n"
        "3. 當需要解析原始資料時，組裝你需要的欄位的 JSON 格式，交給 Q-LLM。\n"
        "4. 驗證 Q-LLM 的輸出格式是否為合法 JSON；若有錯誤，重試或回傳錯誤資訊給 User。\n"
        "5. 維持全域上下文與進度，最後將完整任務結果回傳 User。\n"
        "6. 如果你看到 [HANDLE:xxxxx]，請把它當作「Email / 敏感資訊」，交給 Q-LLM。"
    ),
    sub_agents=[qllm_remote],
)
       # "You are a planner agent. "
       # "When the user asks to summarize, translate, or reason about text, "
       # "you should delegate to qllm_remote by passing the text (as handle)."