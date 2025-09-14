from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# 連線到 Q-LLM 的 A2A
qllm_remote = RemoteA2aAgent(
    name="qllm_remote",
    description="Remote general-purpose Q-LLM agent.",
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)

# P-LLM 規劃代理
planner_agent = Agent(
    model="gemini-1.5-flash",
    name="planner_agent",
    description="Planner agent that delegates reasoning to Q-LLM.",
    instruction=(
        "You are a planner agent. "
        "When the user asks to summarize, translate, or reason about text, "
        "you should delegate to qllm_remote by passing the text (as handle)."
    ),
    sub_agents=[qllm_remote],
)
