from google.adk.agents import LlmAgent

# Q-LLM 定義
qllm_agent = LlmAgent(
    name="qllm",
    model="gemini-2.5-flash",
    instruction=(
        "你是一個隔離 LLM ，專門處理原始資料。"
        "規則：\n"
        "1. 僅根據 P-LLM 提供的任務與需求欄位抽取結構化資訊。\n"
        "2. 缺失填 null。\n"
        "3. 僅輸出單一 JSON 物件，禁止多餘文字或解釋。\n"
        "4. 當你完成任務後 必須把任務回傳給 P-LLM"
    )
)
#uv run uvicorn qllm.server:a2a_app --host 0.0.0.0 --port 8001