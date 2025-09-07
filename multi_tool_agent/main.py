import asyncio
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# ----------------------
# Q-LLM 工具 (代號 → 人名、email args)
# ----------------------
def qllm_parse(user_text: str) -> dict:
    print("[Q-LLM] 收到輸入:", user_text)

    # 模擬代號轉換表
    codebook = {
        "#A12": "alice@example.com",
        "#B77": "bob@example.com",
    }

    recipients = [email for code, email in codebook.items() if code in user_text]

    return {
        "subject": "會議通知",
        "body": "下週一下午三點開會",
        "to": recipients,
    }

qllm_tool = FunctionTool(qllm_parse)

# ----------------------
# send_email 工具
# ----------------------
def send_email(subject: str, body: str, to: list[str]) -> dict:
    print(f"📧 寄信: {subject} / {body} → {to}")
    return {"status": "sent", "to": to}

send_email_tool = FunctionTool(send_email)

# ----------------------
# Callback：存 Q-LLM 結果到 secure 區域
# ----------------------
def after_tool_callback(tool, args, tool_context, tool_response):
    if tool.name == "qllm_parse":
        print(f"[after_tool_callback] 存進 secure 區域: {tool_response}")
        tool_context.state["app:_secure_qllm:send_email"] = tool_response
        return {"status": "stored"}  # 假值回給 P-LLM
    return tool_response

# ----------------------
# 守門員：在呼叫 send_email 前覆蓋 args
# ----------------------
def before_tool_callback(tool, args, tool_context):
    if tool.name == "send_email":
        secure = tool_context.state.get("app:_secure_qllm:send_email")
        if secure:
            print(f"[before_tool_callback] 使用 Q-LLM 結果覆蓋: {secure}")
            # 就地覆蓋參數
            args.update(secure)
    return None  # 確保工具還是會被執行

# ----------------------
# P-LLM Agent
# ----------------------
planner_agent = LlmAgent(
    name="planner",
    model="gemini-1.5-flash",
    instruction=(
        "You are an assistant that sends emails. "
        "Always call qllm_parse first to extract subject, body, and recipients. "
        "Then call send_email using ONLY the parsed result."
    ),
    tools=[qllm_tool, send_email_tool],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)

# ----------------------
# Runner
# ----------------------
async def main():
    session_service = InMemorySessionService()
    runner = Runner(
        app_name="camel_demo",
        session_service=session_service,
        agent=planner_agent,
    )

    session = await session_service.create_session(
        user_id="demo-user", app_name="camel_demo"
    )

    # 測試輸入
    new_message = Content(
        role="user",
        parts=[Part(text="請幫我寄信給 #A12, #B77，標題「會議通知」，內容「下週一下午三點開會」")],
    )

    async for event in runner.run_async(
        user_id="demo-user", session_id=session.id, new_message=new_message
    ):
        print("🟢 Event:", event)

if __name__ == "__main__":
    asyncio.run(main())
