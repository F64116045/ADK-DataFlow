from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.base_agent import BaseAgent
from google.adk.tools.base_tool import BaseTool, ToolContext
from google.genai import types as genai_types
from typing import Any, Optional
import json, re
from .handle_manager import HandleManager


RESET = "\033[0m"
BOLD = "\033[1m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
PURPLE = "\033[95m"
CYAN = "\033[96m"


def resolve_keys(obj: Any, handle_manager: HandleManager) -> Any:
    """遞迴解析 key:xxx → 真值"""
    if isinstance(obj, dict):
        return {k: resolve_keys(v, handle_manager) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_keys(v, handle_manager) for v in obj]
    elif isinstance(obj, str) and obj.startswith("key:"):
        key = obj.split(":", 1)[1]
        try:
            resolved = handle_manager.resolve(key)
            print(f"   {CYAN}Key resolved:{RESET} key:{key} → {type(resolved).__name__}")
            if isinstance(resolved, str) and len(resolved) > 50:
                print(f"   │  Value: {resolved[:50]}...")
            else:
                print(f"   │  Value: {resolved}")
            return resolved
        except KeyError:
            print(f"{YELLOW}Key not found:{RESET} {key} (保持原樣)")
            return obj
    return obj


class KeyPlugin(BasePlugin):
    """流程記錄器 + Store 功能"""

    def __init__(self):
        super().__init__(name="key_plugin")
        self.handle_manager = HandleManager()

    # ========== Before Agent ==========
    async def before_agent_callback(
        self, *, agent: BaseAgent, callback_context: CallbackContext
    ):
        print(f"\n{BOLD}{BLUE} [BeforeAgent]{RESET} {agent.name}")
        print(f"   └─ User Input: {callback_context.user_content}")

    # ========== Before Tool ==========
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict | None:
        print(f"\n{BOLD}{BLUE} [BeforeTool]{RESET} {tool.name}")
        print(f"   └─ Raw Args: {tool_args}")
        
        # 特別顯示 qllm_remote 的 request 內容（還沒 resolve 前）
        if tool.name == "qllm_remote" and "request" in tool_args:
            try:
                req_data = json.loads(tool_args["request"])
                print(f"   └─ Request JSON (Raw):")
                for key, value in req_data.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      {key}: {value[:50]}...")
                    else:
                        print(f"      {key}: {value}")
            except:
                print(f"   └─ Request (raw): {tool_args['request']}")

        # Resolve keys in arguments
        resolved_args = resolve_keys(tool_args, self.handle_manager)

        # 特別處理 qllm_remote 的 JSON request
        if tool.name == "qllm_remote" and "request" in resolved_args:
            req = resolved_args["request"]
            if isinstance(req, str):
                try:
                    print(f"\n{BOLD}{CYAN} [Resolving qllm JSON]{RESET}")
                    data = json.loads(req)
                    # 再次解析 JSON 內部的 keys
                    data = resolve_keys(data, self.handle_manager)
                    resolved_args["request"] = json.dumps(data, ensure_ascii=False)
                    
                    print(f"   └─ Final JSON for qllm:")
                    for key, value in data.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"      {key}: {value[:50]}...")
                        else:
                            print(f"      {key}: {value}")
                except Exception as e:
                    print(f"{RED}JSON parse error:{RESET} {e}")

        # 直接修改 tool_args ，不 return
        if resolved_args != tool_args:
            print(f"\n{BOLD}{CYAN} [In-place Args Modification]{RESET}")
            
            # 清空並重新填入 resolved args
            tool_args.clear()
            tool_args.update(resolved_args)
            
            print(f"   {GREEN} Args modified in-place{RESET}")
            
            # 顯示修改後的最終狀態
            if tool.name == "qllm_remote" and "request" in tool_args:
                try:
                    data = json.loads(tool_args["request"])
                    print(f"   └─ Modified JSON for qllm:")
                    for key, value in data.items():
                        if isinstance(value, str) and len(value) > 50:
                            print(f"      {key}: {value[:50]}...")
                        else:
                            print(f"      {key}: {value}")
                except:
                    pass

        print(f"   {GREEN}Tool will execute with modified args{RESET}")
        return None

    # ========== After Tool ==========
    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: Any,
    ) -> Optional[dict]:
        print(f"\n{BOLD}{GREEN} [AfterTool]{RESET} {tool.name}")
        print(f"   ├─ Input: {tool_args}")
        print(f"   ├─ Output Type: {type(result).__name__}")
        print(f"   └─ Output: {result}")
        
        # 檢查 qllm_remote 是否正常
        if tool.name == "qllm_remote":
            if isinstance(result, dict) and "request" in result:
                print(f"   {RED}  qllm_remote 返回了輸入，沒有實際處理{RESET}")
            else:
                print(f"   {GREEN}✓ qllm_remote 返回了處理結果{RESET}")

        # Store 結果到 HandleManager
        return self._store_result(tool.name, result)

    def _store_result(self, tool_name: str, result: Any) -> Optional[dict]:
        """將工具結果存儲為 keys"""
        if result is None:
            print(f"   {YELLOW}  No result to store{RESET}")
            return None

        print(f"\n{BOLD}{PURPLE} [Storing Result]{RESET}")
        
        # 嘗試解析為 dict
        parsed = None
        if isinstance(result, dict):
            parsed = result
        elif isinstance(result, str):
            try:
                # 清理可能的 markdown 格式
                cleaned = result.strip()
                if cleaned.startswith("```"):
                    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
                    cleaned = re.sub(r"```$", "", cleaned).strip()
                parsed = json.loads(cleaned)
                print(f"   ├─ Parsed JSON from string")
            except Exception as e:
                print(f"   ├─ Failed to parse as JSON: {e}")
                parsed = None

        # 如果是 dict，分別存儲每個欄位
        if isinstance(parsed, dict):
            replaced = {}
            for field, value in parsed.items():
                key = self.handle_manager.save(
                    value, type_hint=f"tool:{tool_name}:{field}"
                )
                replaced[field] = f"key:{key}"
                print(f"   ├─ {GREEN}Stored:{RESET} {field} → key:{key} (type: {type(value).__name__})")
                if isinstance(value, str) and len(value) > 50:
                    print(f"   │  Value: {value[:50]}...")
                else:
                    print(f"   │  Value: {value}")
            
            print(f"   └─ {GREEN}Returning replaced dict{RESET}")
            return replaced

        # 否則存儲整個結果
        key = self.handle_manager.save(result, type_hint=f"tool:{tool_name}")
        print(f"   └─ {GREEN}Stored full result:{RESET} key:{key}")
        return {"output": f"key:{key}"}

    # ========== After Agent ==========
    async def after_agent_callback(self, *, agent, callback_context):
        print(f"\n{BOLD}{YELLOW} [AfterAgent]{RESET} {agent.name}")

        session = callback_context._invocation_context.session
        events = session.events

        last_model_event = next(
            (e for e in reversed(events) if e.content.role == "model"),
            None,
        )
        if not last_model_event:
            print(f"   └─ No model event found")
            return None

        original_content: genai_types.Content = last_model_event.content
        texts = [p.text for p in original_content.parts if getattr(p, "text", None)]
        
        if not texts:
            print(f"   └─ No text parts found")
            return None
            
        full_text = " ".join(texts)
        print(f"   ├─ Original Output: {full_text}")

        # 新功能：Resolve keys in final output
        def replace_key(match):
            key = match.group(1)
            try:
                resolved_value = self.handle_manager.resolve(key)
                print(f"   {CYAN}Final key resolve:{RESET} key:{key} → {type(resolved_value).__name__}")
                
                if isinstance(resolved_value, dict):
                    return json.dumps(resolved_value, ensure_ascii=False, indent=2)
                elif isinstance(resolved_value, (list, tuple)):
                    return json.dumps(resolved_value, ensure_ascii=False)
                else:
                    return str(resolved_value)
            except KeyError:
                print(f"{RED}Key not found in final output:{RESET} {key}")
                return f"key:{key}"

        # 使用正則表達式替換所有 key:xxx
        modified_text = re.sub(r"key:([A-Za-z0-9\-]+)", replace_key, full_text)
        
        if modified_text != full_text:
            print(f"   {GREEN}Final output modified{RESET}")
            print(f"   └─ Resolved Output: {modified_text}")
            return genai_types.Content(parts=[genai_types.Part(text=modified_text)])
        else:
            print(f"   └─ No keys to resolve in final output")
            return None