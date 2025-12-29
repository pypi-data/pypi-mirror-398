import ast
import json
import re

from typing import Union, Any

RE_CODE_BLOCK = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


class JsonParser:
    """Extract json part from text, which encapsulated by ```json ... ``` or ``` ```."""

    def __init__(self):
        pass

    def parse(self, text: str) -> Any:
        match = RE_CODE_BLOCK.search(text)
        if not match:
            return None
        json_str = match.group(1)
        json_obj = None
        try:
            json_obj = json.loads(json_str)
        except json.JSONDecodeError:
            try:
                json_obj = ast.literal_eval(json_str)
            except (SyntaxError, ValueError):
                pass
        return json_obj

    def parse_all(self, text: str) -> list[Any]:
        res: list[Any] = []
        for match in RE_CODE_BLOCK.finditer(text):
            json_str = match.group(1)
            try:
                json_obj = json.loads(json_str)
                res.append(json_obj)
            except json.JSONDecodeError:
                try:
                    json_obj = ast.literal_eval(json_str)
                    res.append(json_obj)
                except (SyntaxError, ValueError):
                    pass
        return res
