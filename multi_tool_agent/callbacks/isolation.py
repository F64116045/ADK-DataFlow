def after_tool_callback(event, ctx):
    if event.tool_name == "qllm_parse":
        # 攔截 Q-LLM 真實輸出，只保留狀態訊號
        event.content = {"status": "ok"}
    return event
