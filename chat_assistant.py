"""
Grok (xAI) chat assistant helpers:
- is_safe_select: heuristic validator for AI-generated SQL
- call_grok_api: REST calls to the xAI API
"""
import json
import requests

from config import XAI_API_KEY, XAI_MODEL, XAI_API_BASE


def is_safe_select(sql_text: str) -> bool:
    """
    Heuristic validator:
    - Allows only SELECT statements (case-insensitive)
    - Disallows dangerous keywords and ';'
    - Ensures generated identifiers are limited to known columns or SQL keywords
    """
    if not sql_text:
        return False
    s = sql_text.strip().lower()
    if not s.startswith("select"):
        return False
    disallowed = ["insert", "update", "delete", "drop", "alter", "create", ";", "attach", "pragma"]
    for kw in disallowed:
        if kw in s:
            return False
    allowed_cols = {"id", "title", "price", "category", "seller_usn", "sold_flag", "image_path", "description", "created_at", "count"}
    words = set(w.strip(",()") for w in s.replace("\n", " ").split())
    sql_keywords = {"select", "from", "where", "group", "by", "order", "limit", "desc", "asc", "count", "as", "and", "or", "on", "join", "having"}
    for w in words:
        # skip purely numeric tokens or tokens with digits/punctuation
        if any(ch.isdigit() for ch in w) or not w.isalpha():
            continue
        if w in sql_keywords or w in allowed_cols:
            continue
        # if it's not a recognized keyword or allowed column, reject
        return False
    return True


def call_grok_api(prompt: str, max_tokens: int = 256, model: str = XAI_MODEL) -> (bool, str):
    """
    Call xAI (Grok) API. Return (ok, text) where ok boolean indicates success.
    We attempt two styles:
      1) POST /v1/responses with {"model": model, "input": prompt}
      2) POST /v1/chat/completions with messages (OpenAI-compatible)
    The function requires XAI_API_KEY to be set (environmentally or in code).
    """
    key = XAI_API_KEY or __import__("os").getenv("XAI_API_KEY")
    if not key:
        return False, "No Grok API key set. Please set XAI_API_KEY environment variable."

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    # Attempt #1: /v1/responses (preferred per xAI docs)
    try:
        url = f"{XAI_API_BASE}/v1/responses"
        payload = {
            "model": model,
            "input": prompt,
            "max_output_tokens": max_tokens
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            j = r.json()
            txt = None
            if isinstance(j.get("output"), list):
                pieces = []
                for out in j["output"]:
                    if isinstance(out.get("content"), list):
                        for c in out["content"]:
                            if isinstance(c, dict) and "text" in c:
                                pieces.append(c["text"])
                            elif isinstance(c, str):
                                pieces.append(c)
                if pieces:
                    txt = "\n".join(pieces)
            if not txt:
                if "result" in j and isinstance(j["result"], str):
                    txt = j["result"]
                elif "text" in j:
                    txt = j["text"]
                else:
                    def find_first_string(obj):
                        if isinstance(obj, str):
                            return obj
                        if isinstance(obj, dict):
                            for v in obj.values():
                                res = find_first_string(v)
                                if res:
                                    return res
                        if isinstance(obj, list):
                            for item in obj:
                                res = find_first_string(item)
                                if res:
                                    return res
                        return None
                    txt = find_first_string(j)
            return True, txt or json.dumps(j)
        else:
            try:
                return False, f"API error {r.status_code}: {r.text}"
            except Exception:
                return False, f"API error {r.status_code}"
    except Exception:
        pass

    # Attempt #2: OpenAI-compatible /v1/chat/completions
    try:
        url2 = f"{XAI_API_BASE}/v1/chat/completions"
        payload2 = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        r2 = requests.post(url2, headers=headers, json=payload2, timeout=30)
        if r2.status_code == 200:
            j = r2.json()
            try:
                return True, j["choices"][0]["message"]["content"]
            except Exception:
                return True, json.dumps(j)
        else:
            return False, f"API error {r2.status_code}: {r2.text}"
    except Exception as e:
        return False, f"Both Grok API attempts failed: {e}"
