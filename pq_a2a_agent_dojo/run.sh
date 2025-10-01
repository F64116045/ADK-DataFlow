#!/bin/bash

# 啟動 Q-LLM server
uv run uvicorn qllm.server:a2a_app --host 0.0.0.0 --port 8001 &

# 等 2 秒確保 server 起來
sleep 5

# 啟動 P-LLM 
uv run -m planner.runner
