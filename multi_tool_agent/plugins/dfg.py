import re
import base64
import urllib.parse
from typing import Dict, List, Any

class DFNode:
    def __init__(self, node_id, value: Any, origin, capabilities=None, taints=None):
        self.node_id = node_id
        self.value = value
        self.origin = origin
        self.capabilities = capabilities or []
        self.taints = set(taints or [])

class DFEdge:
    def __init__(self, src: str, dst: str):
        self.src = src
        self.dst = dst

class DataFlowGraph:
    def __init__(self):
        self.nodes: Dict[str, DFNode] = {}
        self.edges: List[DFEdge] = []

    def add_node(self, node: DFNode):
        self.nodes[node.node_id] = node

    def add_edge(self, src_id: str, dst_id: str, propagate_taint=True):
        self.edges.append(DFEdge(src_id, dst_id))
        if propagate_taint:
            src_node = self.get_node(src_id)
            dst_node = self.get_node(dst_id)
            if src_node and dst_node:
                dst_node.taints.update(src_node.taints)

    def get_node(self, node_id: str) -> DFNode:
        return self.nodes.get(node_id)

    def find_sources(self, node_id: str) -> List[DFNode]:
        """找直接來源節點"""
        return [self.nodes[e.src] for e in self.edges if e.dst == node_id and e.src in self.nodes]

    def trace_sources(self, node_id: str) -> List[DFNode]:
        """遞迴找所有上游來源節點"""
        visited = set()
        result = []
        def dfs(nid):
            for e in self.edges:
                if e.dst == nid and e.src not in visited:
                    visited.add(e.src)
                    src_node = self.nodes.get(e.src)
                    if src_node:
                        result.append(src_node)
                        dfs(e.src)
        dfs(node_id)
        return result

    def _normalize(self, val: str) -> List[str]:
        """生成多種正規化版本以提升比對率"""
        vals = set()
        if not isinstance(val, str):
            try:
                val = str(val)
            except Exception:
                return []
        vals.add(val)
        vals.add(val.lower())
        vals.add(val.strip())
        vals.add(urllib.parse.unquote(val))
        try:
            vals.add(base64.b64decode(val).decode(errors="ignore"))
        except Exception:
            pass
        return list(vals)

    def find_nodes_with_value(self, arg_value):
        """強化版搜尋，包含正規化比對"""
        matches = []
        norm_arg_vals = self._normalize(arg_value)
        for n in self.nodes.values():
            norm_node_vals = self._normalize(n.value)
            if any(a in norm_node_vals for a in norm_arg_vals):
                matches.append(n)
        return matches
