from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class OpenAIChatCompletionsClient:
    base_url: str
    api_key: str
    timeout_s: float = 60.0
    transport: Optional[httpx.BaseTransport] = None

    def translate(
        self, *, text: str, to_locale: str, model: str, custom_instructions: Optional[str] = None
    ) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"

        system = (
            "You are a translation engine. "
            "Translate the user's content to the target locale. "
            "Preserve Markdown structure and formatting. "
            r"Do not translate anything inside placeholders matching '@@MD2LANG_OAI_\d+@@'. "
            "Do not alter those placeholders in any way. "
            "Output ONLY the translated content, with no extra commentary."
        )
        if custom_instructions:
            system += f"\n\nAdditional instructions:\n{custom_instructions}"
        user = f"Target locale: {to_locale}\n\nContent:\n{text}"

        payload: Dict[str, Any] = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout_s, transport=self.transport) as client:
                resp = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e

        if resp.status_code >= 400:
            detail = _safe_extract_error_detail(resp)
            raise RuntimeError(
                f"Translation request failed: HTTP {resp.status_code}{detail}"
            )

        try:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError("Unexpected response format from Chat Completions") from e


def _safe_extract_error_detail(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict):
            err = data.get("error")
            if isinstance(err, dict) and err.get("message"):
                return f": {err['message']}"
        return ""
    except json.JSONDecodeError:
        body = (resp.text or "").strip()
        if body:
            return f": {body[:200]}"
        return ""
