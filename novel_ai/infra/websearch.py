from __future__ import annotations

import json
from typing import Any, Dict, List
from urllib import parse, request

from novel_ai.core.interfaces import WebSearchClient
from novel_ai.infra.config import ApiKeyManager, WebSearchConfig


class GenericWebSearchClient(WebSearchClient):
    """Configurable web search adapter for Reddit/Baidu/custom APIs."""

    def __init__(self, config: WebSearchConfig, key_manager: ApiKeyManager, override_api_key: str | None = None):
        self.config = config
        self.key_manager = key_manager
        self.override_api_key = override_api_key

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        api_key = self.key_manager.key_for_env(self.config.api_key_env, self.override_api_key)
        params = {self.config.query_param: query, "limit": str(limit)}
        qs = parse.urlencode(params)
        url = f"{self.config.api_base}{self.config.search_path}?{qs}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            value = api_key if self.config.api_key_header != "Authorization" else f"Bearer {api_key}"
            headers[self.config.api_key_header] = value

        data = self._get_json(url, headers)
        return self._normalize_results(data)

    def _get_json(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        req = request.Request(url=url, headers=headers, method="GET")
        with request.urlopen(req, timeout=self.config.timeout_s) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)

    def _normalize_results(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        # universal fallbacks
        if "results" in payload and isinstance(payload["results"], list):
            return [self._normalize_item(x) for x in payload["results"]]

        # reddit-like shape
        children = payload.get("data", {}).get("children", [])
        if children:
            items = [x.get("data", {}) for x in children]
            return [self._normalize_item(x) for x in items]

        return []

    def _normalize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": item.get("title") or item.get("name") or "",
            "url": item.get("url") or item.get("permalink") or "",
            "snippet": item.get("snippet") or item.get("selftext") or "",
            "source": str(self.config.provider),
        }
