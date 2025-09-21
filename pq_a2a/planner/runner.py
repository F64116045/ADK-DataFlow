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

    prompt = "london 的溫度是多少"
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