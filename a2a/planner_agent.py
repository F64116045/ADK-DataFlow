import asyncio
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# 連線到 Q-LLM 的 A2A
qllm_remote = RemoteA2aAgent(
    name="qllm_remote",
    description="Remote general-purpose Q-LLM agent.",
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)

# P-LLM：規劃者
planner_agent = Agent(
    model="gemini-1.5-flash",
    name="planner_agent",
    description="Planner agent that delegates reasoning to Q-LLM.",
    instruction=(
        "You are a planner agent. "
        "When the user asks to summarize, translate, or reason about text, "
        "you should delegate to qllm_remote by passing the full text as input."
    ),
    sub_agents=[qllm_remote],
)

# Runner：直接跑 Planner
async def main():
    session_service = InMemorySessionService()
    runner = Runner(app_name="planner_demo", session_service=session_service, agent=planner_agent)

    session = await session_service.create_session(user_id="demo", app_name="planner_demo")

    # 測試任務：Email 總結
    new_message = Content(
        role="user",
        parts=[
            Part(
                text=(
                    "請幫我總結以下 Email：\n\n"
                    "各位團隊成員，\n\n"
                    "明天下午兩點將舉行專案會議，地點在會議室 B。"
                    "屆時會討論三個重點：\n"
                    "1. 上週的進度回顧與問題整理。\n"
                    "2. 下週的開發排程與人力分配。\n"
                    "3. 針對新客戶需求的功能優先順序。\n\n"
                    "請大家準備相關資料，並務必準時出席。\n\n"
                    "謝謝！\n"
                )
            )
        ]
    )


    async for event in runner.run_async(user_id="demo", session_id=session.id, new_message=new_message):
        print("-----------------------------------------------")
        print(" Event:", event)


if __name__ == "__main__":
    asyncio.run(main())
