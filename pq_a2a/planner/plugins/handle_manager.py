import uuid

class HandleManager:
    """簡單的 Key/Value 儲存層，用 HashMap 管理 Value 隔離"""

    def __init__(self):
        self.store = {}

    def save(self, value, type_hint=None):
        key = str(uuid.uuid4())
        self.store[key] = {"value": value, "type": type_hint}
        return key

    def resolve(self, key):
        if key not in self.store:
            raise KeyError(f"Handle {key} 不存在或已過期")
        return self.store[key]["value"]


handle_manager = HandleManager()