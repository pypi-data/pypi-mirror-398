"""Ollama provider implementation for VibeGate LLM integration."""

from __future__ import annotations

import logging
from typing import Any

from vibegate.findings import Finding
from vibegate.llm.cache import LLMCache
from vibegate.llm.prompts import build_combined_prompt
from vibegate.llm.providers import CodeContext, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Ollama-based LLM provider for local model inference."""

    def __init__(
        self,
        model: str = "codellama:7b",
        base_url: str = "http://localhost:11434",
        cache_dir: str | None = None,
        temperature: float = 0.3,
    ):
        """Initialize Ollama provider.

        Args:
            model: Model name (e.g., "codellama:7b", "deepseek-coder:6.7b")
            base_url: Ollama server URL
            cache_dir: Directory for caching LLM responses (default: .vibegate/llm_cache)
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.cache = LLMCache(cache_dir) if cache_dir else None

        # Lazy import to avoid requiring ollama for users who don't use LLM features
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy-load Ollama client."""
        if self._client is None:
            try:
                import ollama

                self._client = ollama.Client(host=self.base_url)
            except ImportError as e:
                raise ImportError(
                    "Ollama client not installed. Install with: pip install ollama"
                ) from e
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama is available and the model is ready.

        Returns:
            True if Ollama is running and model is available
        """
        try:
            # Try to list models to check if Ollama is running
            models = self.client.list()
            model_names = [m["name"] for m in models.get("models", [])]

            # Check if our specific model is available
            if self.model not in model_names:
                # Try base model name without tag
                base_name = self.model.split(":")[0]
                if not any(base_name in name for name in model_names):
                    logger.warning(
                        f"Model {self.model} not found in Ollama. Available models: {model_names}"
                    )
                    return False

            return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def get_model_info(self) -> dict[str, str]:
        """Get information about the current model.

        Returns:
            Dictionary with model metadata
        """
        try:
            model_info = self.client.show(self.model)
            return {
                "name": self.model,
                "family": model_info.get("details", {}).get("family", "unknown"),
                "parameter_size": model_info.get("details", {}).get(
                    "parameter_size", "unknown"
                ),
                "quantization": model_info.get("details", {}).get(
                    "quantization_level", "unknown"
                ),
            }
        except Exception as e:
            logger.debug(f"Could not get model info: {e}")
            return {"name": self.model, "error": str(e)}

    def explain_finding(self, finding: Finding) -> str:
        """Generate a user-friendly explanation of a finding.

        Args:
            finding: The finding to explain

        Returns:
            Plain-English explanation
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get_explanation(finding.fingerprint, self.model)
            if cached:
                return cached

        # Build prompt and call LLM
        from vibegate.llm.prompts import build_explanation_prompt

        prompt = build_explanation_prompt(finding)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": self.temperature},
            )
            explanation = response["response"].strip()

            # Cache the result
            if self.cache:
                self.cache.save_explanation(
                    finding.fingerprint, self.model, explanation
                )

            return explanation

        except Exception as e:
            logger.error(f"Failed to generate explanation: {e}")
            return f"Error generating explanation: {str(e)}"

    def generate_fix_prompt(self, finding: Finding, context: CodeContext) -> str:
        """Generate a detailed fix prompt for AI coding assistants.

        Args:
            finding: The finding to fix
            context: Code context

        Returns:
            Detailed fix prompt
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get_fix_prompt(finding.fingerprint, self.model)
            if cached:
                return cached

        # Build prompt and call LLM
        from vibegate.llm.prompts import build_fix_prompt

        prompt = build_fix_prompt(finding, context)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": self.temperature},
            )
            fix_prompt = response["response"].strip()

            # Cache the result
            if self.cache:
                self.cache.save_fix_prompt(finding.fingerprint, self.model, fix_prompt)

            return fix_prompt

        except Exception as e:
            logger.error(f"Failed to generate fix prompt: {e}")
            return f"Error generating fix prompt: {str(e)}"

    def process_finding(
        self, finding: Finding, context: CodeContext | None = None
    ) -> LLMResponse:
        """Process a finding and generate both explanation and fix prompt.

        This is more efficient than calling explain_finding and generate_fix_prompt
        separately, as it makes a single LLM call.

        Args:
            finding: The finding to process
            context: Optional code context

        Returns:
            LLMResponse with both explanation and fix prompt
        """
        # Check cache first
        cached_response = None
        if self.cache:
            cached_response = self.cache.get_combined(finding.fingerprint, self.model)
            if cached_response:
                return LLMResponse(
                    explanation=cached_response["explanation"],
                    fix_prompt=cached_response["fix_prompt"],
                    model_used=self.model,
                    cached=True,
                )

        # Build combined prompt and call LLM
        prompt = build_combined_prompt(finding, context)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": self.temperature},
            )
            content = response["response"].strip()

            # Parse the response into explanation and fix prompt sections
            explanation, fix_prompt = self._parse_combined_response(content)

            # Cache the result
            if self.cache:
                self.cache.save_combined(
                    finding.fingerprint, self.model, explanation, fix_prompt
                )

            return LLMResponse(
                explanation=explanation,
                fix_prompt=fix_prompt,
                model_used=self.model,
                cached=False,
            )

        except Exception as e:
            logger.error(f"Failed to process finding: {e}")
            return LLMResponse(
                explanation=f"Error: {str(e)}",
                fix_prompt=f"Error: {str(e)}",
                model_used=self.model,
                cached=False,
            )

    def _parse_combined_response(self, content: str) -> tuple[str, str]:
        """Parse combined LLM response into explanation and fix prompt.

        Args:
            content: Raw LLM response

        Returns:
            Tuple of (explanation, fix_prompt)
        """
        # Look for section headers
        explanation = ""
        fix_prompt = ""

        if "## EXPLANATION" in content and "## FIX PROMPT" in content:
            parts = content.split("## FIX PROMPT")
            explanation = parts[0].replace("## EXPLANATION", "").strip()
            fix_prompt = parts[1].strip()
        elif "EXPLANATION:" in content and "FIX PROMPT:" in content:
            parts = content.split("FIX PROMPT:")
            explanation = parts[0].replace("EXPLANATION:", "").strip()
            fix_prompt = parts[1].strip()
        else:
            # Fallback: treat entire response as explanation
            explanation = content
            fix_prompt = "See explanation above for guidance on fixing this issue."

        return explanation, fix_prompt

    def pull_model(self) -> bool:
        """Pull/download the model if not already available.

        Returns:
            True if model was pulled successfully or already exists
        """
        try:
            logger.info(f"Pulling model {self.model}...")
            self.client.pull(self.model)
            logger.info(f"Model {self.model} ready")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {self.model}: {e}")
            return False
