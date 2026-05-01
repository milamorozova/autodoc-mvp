from __future__ import annotations

"""
tools/llm_client.py

Клиент для OpenRouter API (OpenAI-совместимый формат).
Бесплатные модели: openrouter/auto, google/gemini-2.0-flash-exp:free

Переменная окружения: OPENROUTER_API_KEY
Или передаётся явно через аргумент api_key=...
"""

import os
import json
import http.client
import ssl
from typing import Optional


OPENROUTER_HOST  = "openrouter.ai"
OPENROUTER_PATH  = "/api/v1/chat/completions"
OPENROUTER_MODEL = "openrouter/auto"

MAX_OUTPUT_TOKENS = 4096


def _make_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    try:
        return ssl.create_default_context()
    except Exception:
        pass
    return ssl._create_unverified_context()


def call_llm(
    prompt: str,
    api_key: Optional[str] = None,
    max_tokens: int = MAX_OUTPUT_TOKENS,
) -> str:
    """
    Отправляет prompt в OpenRouter и возвращает текст ответа.

    Raises:
        EnvironmentError: если ключ не найден.
        RuntimeError: если API вернул ошибку.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY не задан. "
            "Установи переменную окружения или передай --api-key явно."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    ssl_ctx    = _make_ssl_context()

    conn = http.client.HTTPSConnection(OPENROUTER_HOST, timeout=60, context=ssl_ctx)
    try:
        conn.request(
            "POST",
            OPENROUTER_PATH,
            body=body_bytes,
            headers={
                "Content-Type":  "application/json; charset=utf-8",
                "Authorization": "Bearer {}".format(key),
                "Content-Length": str(len(body_bytes)),
                "HTTP-Referer":  "https://github.com/autodoc-mvp",
                "X-Title":       "AutoDoc MVP",
            },
        )
        resp = conn.getresponse()
        raw  = resp.read().decode("utf-8")
    finally:
        conn.close()

    if resp.status != 200:
        raise RuntimeError(
            "OpenRouter API вернул ошибку {}: {}".format(resp.status, raw)
        )

    body = json.loads(raw)

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(
            "Неожиданная структура ответа OpenRouter: {}".format(body)
        )