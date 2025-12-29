# sdk/codexasi.py
from __future__ import annotations
import bootstrap_project_root  # noqa: F401

from typing import Dict, Any
from capability_envelope.multi_domain import synthesize, default_meta

class CodexASIClient:
    def __init__(self, model: str = "llama3", role: str = "trusted"):
        self.model = model
        self.role = role

    def run(self, prompt: str, domain: str = "general", meta: Dict[str, Any] | None = None) -> str:
        m = default_meta()
        m["model"] = self.model
        m["role"] = self.role
        m["domain"] = domain
        if meta:
            m.update(meta)
        return synthesize(prompt, meta=m)
