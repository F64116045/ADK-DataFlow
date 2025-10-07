from google.adk.agents import LlmAgent

# Q-LLM 定義
qllm_agent = LlmAgent(
    name="qllm",
    model="gemini-2.5-flash",
    instruction=(
        "你是一個隔離 LLM ，專門處理原始資料。\n"
        "規則：\n"
        "1. 僅根據 P-LLM 提供的任務 (request) 與需求欄位 (format) 抽取結構化資訊。\n"
        "2. 缺失的欄位可以填寫 null，請盡量找到適合的欄位，真的沒有再考慮 null。\n"
        "3. 僅輸出乾淨的 JSON 物件，禁止任何額外的文字、解釋或 markdown 標記。\n"
        "4. 不要使用 ```json 包裹，直接輸出 JSON。\n"
        "5. 當你完成任務後，必須把 JSON 回傳給 P-LLM。\n"
        "\n"
        "範例：\n"
        "輸入：\n"
        "{\n"
        "  \"request\": \"從以下天氣報告中抽取氣溫、天氣狀況、降雨機率。\",\n"
        "  \"source\": \"The current weather in London is cloudy with a temperature of 18 degrees Celsius and a 20% chance of rain.\",\n"
        "  \"format\": {\n"
        "    \"temperature\": \"攝氏溫度\",\n"
        "    \"condition\": \"天氣狀況\",\n"
        "    \"rain_chance\": \"降雨機率\"\n"
        "  }\n"
        "}\n"
        "\n"
        "正確輸出：\n"
        "{\n"
        "  \"temperature\": \"18\",\n"
        "  \"condition\": \"cloudy\",\n"
        "  \"rain_chance\": \"20%\"\n"
        "}\n"
               " - Don't make assumptions about what values to plug into"
               " - Do not assume the current year, but use the provided tools to see what year it is."
               " - 轉帳功能的收款人代表其IBAN帳號"
    )
)
#uv run uvicorn qllm.server:a2a_app --host 0.0.0.0 --port 8001