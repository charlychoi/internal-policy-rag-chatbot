from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import requests


@dataclass
class OpenNotebookConfig:
    api_base: str = os.getenv("OPEN_NOTEBOOK_API_BASE", "http://localhost:5055/api")
    password: str = os.getenv("OPEN_NOTEBOOK_PASSWORD", "")
    notebook_id: str = os.getenv("OPEN_NOTEBOOK_NOTEBOOK_ID", "")
    strategy_model: str = os.getenv("OPEN_NOTEBOOK_STRATEGY_MODEL", "")
    answer_model: str = os.getenv("OPEN_NOTEBOOK_ANSWER_MODEL", "")
    final_answer_model: str = os.getenv("OPEN_NOTEBOOK_FINAL_ANSWER_MODEL", "")
    timeout: int = 60


class OpenNotebookClient:
    """Small HTTP adapter around Open Notebook's REST API.

    The PoC intentionally keeps this adapter thin so the app can run with a
    mock/fallback retriever when Open Notebook is not available.
    """

    def __init__(self, config: OpenNotebookConfig | None = None):
        self.config = config or OpenNotebookConfig()
        self.api_base = self.config.api_base.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.config.password:
            headers["Authorization"] = f"Bearer {self.config.password}"
        return headers

    def health(self) -> bool:
        try:
            response = requests.get(f"{self.api_base}/models", headers=self.headers, timeout=5)
            return response.status_code < 500
        except requests.RequestException:
            return False

    def create_notebook(self, name: str, description: str = "") -> dict[str, Any]:
        response = requests.post(
            f"{self.api_base}/notebooks",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"name": name, "description": description},
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def upload_source(self, file_path: Path, notebook_id: str | None = None, title: str | None = None) -> dict[str, Any]:
        notebook_id = notebook_id or self.config.notebook_id
        if not notebook_id:
            raise ValueError("notebook_id is required for Open Notebook source upload")
        with file_path.open("rb") as f:
            response = requests.post(
                f"{self.api_base}/sources",
                headers=self.headers,
                data={
                    "type": "upload",
                    "notebook_id": notebook_id,
                    "title": title or file_path.name,
                    "embed": "true",
                    "async_processing": "true",
                },
                files={"file": (file_path.name, f)},
                timeout=self.config.timeout,
            )
        response.raise_for_status()
        return response.json()

    def get_source_status(self, source_id: str) -> dict[str, Any]:
        response = requests.get(f"{self.api_base}/sources/{source_id}/status", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, search_type: str = "vector", limit: int = 5) -> dict[str, Any]:
        response = requests.post(
            f"{self.api_base}/search",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "query": query,
                "type": search_type,
                "limit": limit,
                "search_sources": True,
                "search_notes": False,
                "minimum_score": 0.2,
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()

    def ask_simple(self, question: str) -> dict[str, Any]:
        missing = [
            name for name, value in {
                "strategy_model": self.config.strategy_model,
                "answer_model": self.config.answer_model,
                "final_answer_model": self.config.final_answer_model,
            }.items() if not value
        ]
        if missing:
            raise ValueError(f"Missing Open Notebook model ids: {', '.join(missing)}")
        response = requests.post(
            f"{self.api_base}/search/ask/simple",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "question": question,
                "strategy_model": self.config.strategy_model,
                "answer_model": self.config.answer_model,
                "final_answer_model": self.config.final_answer_model,
            },
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        return response.json()
