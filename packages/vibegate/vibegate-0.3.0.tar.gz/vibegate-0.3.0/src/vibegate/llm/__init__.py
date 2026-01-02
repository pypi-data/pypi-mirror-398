"""LLM integration for VibeGate - local models for explaining findings and generating fix prompts."""

from __future__ import annotations

from vibegate.llm.providers import LLMProvider, CodeContext, LLMResponse
from vibegate.llm.ollama import OllamaProvider
from vibegate.llm.cache import LLMCache

__all__ = ["LLMProvider", "OllamaProvider", "CodeContext", "LLMResponse", "LLMCache"]
