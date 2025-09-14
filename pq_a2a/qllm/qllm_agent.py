from google.adk.agents import LlmAgent

# Q-LLM 定義
qllm_agent = LlmAgent(
    name="qllm",
    model="gemini-1.5-flash",
    instruction="You are Q-LLM. You take full text values and return structured outputs safely."
)
