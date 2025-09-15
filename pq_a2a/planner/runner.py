import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types

from planner.planner_agent import planner_agent
from planner.plugins.printflow_plugin import PrintFlowPlugin
from planner.plugins.handle_plugin import HandleManagerPlugin
from planner.plugins.key_plugin import KeyPlugin

async def main():
    runner = InMemoryRunner(
        agent=planner_agent,
        app_name="pq_a2a_demo",
        plugins=[KeyPlugin()],
    )

    session = await runner.session_service.create_session(
        user_id="user",
        app_name="pq_a2a_demo",
    )

    prompt = """我收到一封同事寄來的 Email，裡面有下週部門聚會的資訊。
        請幫我整理出活動的日期、時間、地點，以及寄件人和收件人。

        以下是 Email 原文：

        From: Kevin Lin <kevin_lin(at)company.com>
        To: marketing-team@company.com; Alice <alice.wu@company.com>
        Cc: manager@company.com
        Date: Thu, Sept 11, 2025 08:45 AM
        Subject: 部門聚餐

        Hi all,

        下週我們部門要來個小聚會，時間地點如下：

        日期：9/18（星期四）
        時間：晚上 6 點開始
        地點：台北市大安區和平東路 123 號「老地方熱炒店」

        大家可以帶家人一起來，餐費公司會補助一部分。
        如果有任何飲食禁忌，記得提前告訴我。

        See you there!
        Kevin
        """
    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=types.Content(
            role="user", parts=[types.Part.from_text(text=prompt)]
        ),
    ):
        print(f"[Event] From {event.author}: {event.content}")

if __name__ == "__main__":
    asyncio.run(main())
#uv run -m planner.runner