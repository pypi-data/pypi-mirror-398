#!/usr/bin/env python
# coding: utf-8

import json


from athenah_ai.logger import logger

def remove_code_fences(value: str) -> int:
    value = value.replace(" ", "").strip()
    return value.replace("```json", "").replace("```", "")

def safe_json_loads(s: str):
    """
    Attempts to extract and load valid JSON from a string.
    If not possible, returns None.
    """
    try:
        if isinstance(s, dict):
            # If input is already a dictionary, return it as is
            return s
        # Remove code block markers and language hints
        s = s.strip()
        if s.startswith("```"):
            s = s.lstrip("`")
            # Remove language hint if present
            if s.startswith("json"):
                s = s[4:]
            s = s.strip()
        # Remove trailing code block if present
        if s.endswith("```"):
            s = s[:-3].strip()
        return json.loads(s)
    except Exception as e:
        logger.error(f"safe_json_loads error: {e} | input: {s}")
        return {}