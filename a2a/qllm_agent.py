from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Q-LLM: General purpose LLM
qllm_agent = LlmAgent(
    name="qllm",
    model="gemini-1.5-flash",
    instruction="You are Q-LLM, a general-purpose assistant that can summarize, translate, or reason over text safely."
)

# Wrap into A2A server
a2a_app = to_a2a(qllm_agent, port=8001)

#uv run uvicorn qllm_agent:a2a_app --host 0.0.0.0 --port 8001
#curl http://localhost:8001/.well-known/agent-card.json