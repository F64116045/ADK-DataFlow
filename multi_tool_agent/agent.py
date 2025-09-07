from google.adk.agents import LlmAgent

planner_agent = LlmAgent(
    name="planner",
    model="gemini-pro",
    system_prompt=(
        "You are a planner. "
        "Always call qllm_parse first, then create_event."
    )
)
