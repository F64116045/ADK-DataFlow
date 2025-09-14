from google.adk.a2a.utils.agent_to_a2a import to_a2a
from qllm.qllm_agent import qllm_agent

# 把 Q-LLM 包成 A2A server
a2a_app = to_a2a(qllm_agent, port=8001)
