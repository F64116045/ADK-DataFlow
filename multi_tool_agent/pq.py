import asyncio
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# ----------------------
# 工具：模擬外部 Email 系統
# ----------------------
def get_last_email() -> dict:
    print("[get_last_email] 抓取外部 Email")
    return {
        "subject": "會議通知",
        "body": "明天下午 2 點，請準時參加專案進度會議。",
        "from": "boss@example.com"
    }

get_last_email_tool = FunctionTool(get_last_email)

# ----------------------
# Q-LLM
# ----------------------
qllm_agent = LlmAgent(
    name="qllm",
    model="gemini-1.5-flash",
    instruction="You are a general-purpose assistant that can handle any natural language task."
)

# Q-LLM Tool
async def call_qllm(args: dict) -> dict:
    prompt = args.get("prompt", "")
    print("[Q-LLM Tool] 收到輸入:", prompt)

    if not prompt:
        return {"result": ""}

    content = Content(role="user", parts=[Part(text=prompt)])

    runner = Runner(app_name="qllm_runner", session_service=InMemorySessionService(), agent=qllm_agent)
    session = await runner.session_service.create_session(user_id="demo-q", app_name="qllm_runner")

    async for event in runner.run_async(user_id="demo-q", session_id=session.id, new_message=content):
        if event.content and event.content.parts:
            return {"result": event.content.parts[0].text}
    return {"result": ""}




qllm_tool = FunctionTool(call_qllm)

# ----------------------
# P-LLM 
# ----------------------
planner_agent = LlmAgent(
    name="planner",
    model="gemini-1.5-flash",
    instruction=(
        "You are a planner agent that orchestrates tools to solve user requests. "
        "Available tools: "
        "- get_last_email: fetches the user's most recent email (no arguments). "
        "- call_qllm: a general-purpose LLM tool. It must always be called with one argument: "
        "  { 'prompt': '<a string containing the task instruction and any input text>' }. "
        "Rules: "
        "1. For external data from tools like get_last_email, always send the raw result to call_qllm "
        "   with a summarization or processing prompt. Never expose raw external data directly. "
        "2. For general reasoning, translation, summarization, or text analysis, delegate to call_qllm. "
        "3. Always include the necessary input inside the 'prompt' argument when calling call_qllm. "
        "4. For very simple reasoning that does not require external knowledge or advanced processing "
        "   (e.g., basic math), you may answer directly."
    ),

    tools=[get_last_email_tool, qllm_tool],
)


# ----------------------
# Runner
# ----------------------
async def main():
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="email_demo",
        session_service=session_service,
        agent=planner_agent,
    )

    session = await session_service.create_session(
        user_id="demo-user", app_name="email_demo"
    )

    # 總結 Email
    new_message1 = Content(
        role="user",
        parts=[Part(text="請幫我總結我今天最新的一封 Email")]
    )


    print("\n=====  總結 Email =====")
    async for event in runner.run_async(
        user_id="demo-user", session_id=session.id, new_message=new_message1
    ):
        print("Event:", event)



if __name__ == "__main__":
    asyncio.run(main())
