# multi_tool_agent/plugins/policies.py
import yaml
import os

CAP_PATH = os.path.join(os.path.dirname(__file__), "capabilities.yaml")

with open(CAP_PATH, "r", encoding="utf-8") as f:
    CAP_CONFIG = yaml.safe_load(f)

def is_tool_allowed(tool_name, taints):
    allowed_caps = set(CAP_CONFIG["tools"].get(tool_name, {}).get("allow", []))
    return bool(allowed_caps.intersection(taints))  # 有交集才允許
