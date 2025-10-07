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

TYPE_MAP = {
    "int": int,
    "integer": int,
    "float": float,
    "number": (int, float),
    "string": str,
    "str": str,
    "bool": bool,
    "boolean": bool,
    "object": dict,
    "array": list,
    "list": list,
}


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
    # ========== Before Tool ==========
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict | None:
        print(f"\n{BOLD}{BLUE}[BeforeTool]{RESET} {tool.name}")
        print(f"   └─ Raw Args: {tool_args}")

        # 🔹 Step 1. 遞迴解析所有 key:xxx → 真值
        resolved_args = resolve_keys(tool_args, self.handle_manager)

        # 🔹 Step 2. 若為 qllm_remote，進一步處理 request
        if tool.name == "qllm_remote" and "request" in resolved_args:
            req = resolved_args["request"]

            print(f"\n{BOLD}{CYAN}[Processing qllm_remote.request]{RESET}")

            # --- Case 1: request 是 dict（尚未序列化） ---
            if isinstance(req, dict):
                print(f"   ├─ Detected dict input → serializing to JSON string")
                resolved_args["request"] = json.dumps(req, ensure_ascii=False, indent=None)

            # --- Case 2: request 是 JSON 字串，嘗試反序列化後再轉回 ---
            elif isinstance(req, str):
                try:
                    data = json.loads(req)
                    print(f"   ├─ Parsed request JSON successfully")
                    # 解析內部的 key:xxx
                    data = resolve_keys(data, self.handle_manager)
                    resolved_args["request"] = json.dumps(data, ensure_ascii=False, indent=None)
                except Exception as e:
                    print(f"   {YELLOW}└─ Skipped: request is plain string or invalid JSON ({e}){RESET}")
            else:
                print(f"   {YELLOW}└─ Unsupported request type ({type(req).__name__}), ignoring{RESET}")

            # 顯示最終 JSON
            try:
                parsed = json.loads(resolved_args["request"])
                print(f"   └─ Final request JSON for qllm:")
                for k, v in parsed.items():
                    preview = (v[:80] + "...") if isinstance(v, str) and len(v) > 80 else v
                    print(f"      {k}: {preview}")
            except Exception:
                print(f"   {YELLOW}└─ Unable to pretty-print final request{RESET}")

        # 🔹 Step 3. 更新 tool_args（原地修改）
        if resolved_args != tool_args:
            print(f"\n{BOLD}{CYAN}[In-place Args Modification]{RESET}")
            tool_args.clear()
            tool_args.update(resolved_args)
            print(f"   {GREEN}Args modified in-place{RESET}")

        # 🔹 Step 4. 顯示最終狀態
        if tool.name == "qllm_remote" and "request" in tool_args:
            try:
                data = json.loads(tool_args["request"])
                print(f"   └─ Verified final JSON structure:")
                for key, value in data.items():
                    if isinstance(value, str) and len(value) > 50:
                        print(f"      {key}: {value[:50]}...")
                    else:
                        print(f"      {key}: {value}")
            except Exception:
                print(f"   {YELLOW}└─ Request remains as plain string{RESET}")

        print(f"   {GREEN}Tool will execute with modified args{RESET}")
        return None



    # ========== format CHECKING ==========
    import json, re
    from datetime import datetime

    def _validate_qllm_schema(self, tool_args: dict, result: dict):
        try:
            req_json = json.loads(tool_args.get("request", "{}"))
            expected_format = req_json.get("format", {})

            # --- Step 1: 抽取 JSON 片段 ---
            if isinstance(result, str):
                # 去掉 code fence
                clean = re.sub(r"^```(?:json)?", "", result.strip(), flags=re.I)
                clean = re.sub(r"```$", "", clean.strip(), flags=re.I)
                # 只取 { ... }
                m = re.search(r"\{[\s\S]*\}", clean)
                if m:
                    result = m.group(0)
            # --- Step 2: 嘗試解析 ---
            if isinstance(result, str):
                result = json.loads(result)

            errors = []
            coerced = {}

            # --- Step 3: 型別檢查與轉型 ---
            for field, typ in expected_format.items():
                val = result.get(field)
                if val is None:
                    errors.append(f"Missing field: {field}")
                    coerced[field] = None
                    continue

                if typ == "float":
                    try:
                        coerced[field] = float(val)
                    except:
                        errors.append(f"Field '{field}' expected float, got {val}")
                        coerced[field] = None
                elif typ == "string":
                    if field.lower() == "date":
                        # 嘗試正規化日期
                        try:
                            dt = datetime.strptime(str(val), "%Y-%m-%d")
                            coerced[field] = dt.strftime("%Y-%m-%d")
                        except:
                            # 嘗試 Month Year → YYYY-MM-01
                            try:
                                dt = datetime.strptime(str(val), "%B %Y")
                                coerced[field] = dt.strftime("%Y-%m-01")
                            except:
                                coerced[field] = str(val)
                    else:
                        coerced[field] = str(val)
                else:
                    coerced[field] = val

            if errors:
                print("[SchemaCheck] Errors:")
                for e in errors:
                    print("  -", e)
                return False

            print("[SchemaCheck] All fields match expected types ✔")
            return True

        except Exception as e:
            print("[SchemaCheck] Error validating schema:", e)
            return False




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
            ok = self._validate_qllm_schema(tool_args, result)
            if not ok:
                raise ValueError(f"Q-LLM 回傳的資料不符合格式或型別要求！")

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

        try:
            session = callback_context._invocation_context.session
            events = getattr(session, "events", [])

            # 找到最後一個 model event（要防止 e.content 為 None）
            last_model_event = next(
                (e for e in reversed(events) if e.content and getattr(e.content, "role", None) == "model"),
                None,
            )

            if not last_model_event:
                print(f"   └─ No model event found")
                return None

            original_content: genai_types.Content = last_model_event.content

            # 收集 text parts
            texts = [p.text for p in getattr(original_content, "parts", []) if getattr(p, "text", None)]
            if not texts:
                print(f"   └─ No text parts found")
                return None

            full_text = " ".join(texts)
            print(f"   ├─ Original Output: {full_text}")

            # ========== Key Resolve ==========
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

            # 替換所有 key:xxxx
            modified_text = re.sub(r"key:([A-Za-z0-9\-]+)", replace_key, full_text)

            if modified_text != full_text:
                print(f"   {GREEN}Final output modified{RESET}")
                print(f"   └─ Resolved Output: {modified_text}")
                return genai_types.Content(parts=[genai_types.Part(text=modified_text)])
            else:
                print(f"   └─ No keys to resolve in final output")
                return None

        except Exception as e:
            print(f"{RED}[AfterAgent Error]{RESET} {e}")
            return None