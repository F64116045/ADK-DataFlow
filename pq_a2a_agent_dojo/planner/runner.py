# runner.py
import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types

from planner.planner_agent import planner_agent
from planner.plugins.printflow_plugin import PrintFlowPlugin
from planner.plugins.handle_plugin import HandleManagerPlugin
from planner.plugins.key_plugin import KeyPlugin


async def chat_loop():
    runner = InMemoryRunner(
        agent=planner_agent,
        app_name="banking_assistant",
        plugins=[KeyPlugin()],
    )

    # 建立 session
    session = await runner.session_service.create_session(
        user_id="user123",
        app_name="banking_assistant",
    )

    print("銀行 Agent 已啟動！")
    print("可用功能：查詢餘額、查看交易記錄、支付帳單、排程交易、天氣查詢等")
    print("輸入 'exit' 或 'quit' 結束對話\n")

    while True:
        try:
            user_input = input("User: ").strip()
            
            if user_input.lower() in ["exit", "quit", "退出"]:
                print("感謝使用銀行Agent，再見！")
                break
            
            if not user_input:
                continue

            # 執行對話
            print("\nLLM Agent: ", end="", flush=True)
            
            async for event in runner.run_async(
                user_id="user123",
                session_id=session.id,
                new_message=types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text=user_input)]
                ),
            ):
                if event.content and hasattr(event.content, 'text'):
                    print(event.content.text, end="", flush=True)
            
            print("\n")  # 結束回應後換行

        except KeyboardInterrupt:
            print("\n\n再見")
            break
        except Exception as e:
            print(f"\n發生錯誤: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(chat_loop())
#uv run -m planner.runner