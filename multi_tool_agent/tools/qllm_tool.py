from google.adk.tools import tool

@tool
async def qllm_parse(user_input: str, schema: dict, ctx) -> str:
    # 模擬呼叫 Q-LLM，回傳結構化 JSON
    result = {
        "title": "Meeting",
        "time": "2025-09-10T14:00:00",
        "participants": ["Alice", "Bob"]
    }
    # 存進 session state
    ctx.session.state["parsed_data"] = result
    # 回傳 dummy 值，避免洩漏
    return "__QLLM_OK__"
