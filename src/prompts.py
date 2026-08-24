import json
import re
from typing import List, Optional, Dict, Any, Tuple


class PromptManager:
    """轻量 prompt 管理器，支持模块激活和系统提示生成。"""

    MODULE_TOOLS: Dict[str, List[str]] = {
        "game": ["game_move"],
    }

    def __init__(self, active_modules: Optional[List[str]] = None):
        self._active_modules: set = set()
        self._base_content: str = "You are a concise game programming assistant, answer questions directly."
        self._module_contents: Dict[str, str] = {
            "game": "Need to make correct movement actions based on game rules.",
        }
        if active_modules:
            for m in active_modules:
                if m in self.MODULE_TOOLS:
                    self._active_modules.add(m)

    def get_active_tool_names(self) -> List[str]:
        tool_names = set()
        for module in self._active_modules:
            tool_names.update(self.MODULE_TOOLS.get(module, []))
        return sorted(tool_names)

    def get_system_prompt(self, tools: Optional[List[str]] = None) -> str:
        parts = [self._base_content]
        for module_name in sorted(self._active_modules):
            content = self._module_contents.get(module_name, "")
            if content:
                parts.append(content)

        if tools is not None:
            active_tool_names = tools
        else:
            active_tool_names = self.get_active_tool_names()

        if active_tool_names:
            parts.append("**Available Tools:**")
            for name in active_tool_names:
                parts.append(f"- {name}: Execute game movement actions, params include move_data")

        return "\n\n".join(parts)


def _find_complete_json_objects(text: str) -> List[Tuple[int, int]]:
    positions = []
    i = 0
    n = len(text)
    while i < n:
        start = text.find('{', i)
        if start == -1:
            break

        brace_count = 1
        end = start + 1
        in_string = False
        escape = False

        while end < n and brace_count > 0:
            char = text[end]
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = not in_string
            elif not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
            end += 1

        if brace_count == 0:
            positions.append((start, end - 1))
        i = end
    return positions


def _process_tool_obj(obj: Dict[str, Any]) -> Dict[str, Any]:
    reserved_keys = {"tool", "params"}
    if "params" not in obj:
        obj["params"] = {}
    top_level_params = {k: v for k, v in obj.items() if k not in reserved_keys}
    if top_level_params:
        if not isinstance(obj["params"], dict):
            obj["params"] = {}
        obj["params"].update(top_level_params)
        for k in top_level_params:
            del obj[k]
    if isinstance(obj.get("params"), dict) and "params" in obj["params"]:
        nested_params = obj["params"].pop("params")
        if isinstance(nested_params, dict):
            obj["params"].update(nested_params)
    return obj


def _fix_unescaped_newlines(json_str: str) -> str:
    result = []
    i = 0
    n = len(json_str)
    in_string = False
    escape = False
    while i < n:
        char = json_str[i]
        if escape:
            result.append(char)
            escape = False
        elif char == '\\':
            result.append(char)
            escape = True
        elif char == '"':
            in_string = not in_string
            result.append(char)
        elif in_string and char == '\n':
            result.append('\\n')
        elif in_string and char == '\r':
            pass
        elif in_string and char == '\t':
            result.append('\\t')
        else:
            result.append(char)
        i += 1
    return ''.join(result)


def _regex_fallback_parse(text: str) -> Optional[Dict[str, Any]]:
    tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', text)
    if not tool_match:
        return None
    tool_name = tool_match.group(1)
    params = {}
    common_params = ["path", "command", "query", "timeout", "skill", "action", "index",
                     "status", "question", "code", "file", "sheet", "content", "url",
                     "module", "topic", "message", "summary", "history", "skill_name",
                     "mode", "type", "value", "target", "source", "output", "input",
                     "config", "data", "key", "name", "move_data"]
    for param_name in common_params:
        pattern = rf'"{param_name}"\s*:\s*"([^"]+)"'
        match = re.search(pattern, text)
        if match:
            params[param_name] = match.group(1)
    timeout_match = re.search(r'"timeout"\s*:\s*(\d+)', text)
    if timeout_match:
        params["timeout"] = int(timeout_match.group(1))
    index_match = re.search(r'"index"\s*:\s*(\d+)', text)
    if index_match:
        params["index"] = int(index_match.group(1))
    if params:
        return {"tool": tool_name, "params": params}
    return {"tool": tool_name, "params": {}}


def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """从 LLM 回复中解析工具调用。支持多种格式：JSON 对象、代码块、文本混合。"""
    try:
        if "tool" not in text:
            return None

        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        text = re.sub(r'\n?```\s*$', '', text)
        text = text.strip()

        json_positions = _find_complete_json_objects(text)
        for start, end in reversed(json_positions):
            try:
                json_str = text[start:end+1]
                obj = json.loads(json_str)
                if isinstance(obj, dict) and "tool" in obj:
                    return _process_tool_obj(obj)
            except json.JSONDecodeError:
                try:
                    fixed = _fix_unescaped_newlines(text[start:end+1])
                    obj = json.loads(fixed)
                    if isinstance(obj, dict) and "tool" in obj:
                        return _process_tool_obj(obj)
                except Exception:
                    continue

        result = _regex_fallback_parse(text)
        if result:
            return result
    except Exception as e:
        print(f"Error parsing tool call: {e}")
    return None
