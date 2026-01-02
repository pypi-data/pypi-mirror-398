"""Caching layer for LLM responses to avoid redundant inference."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMCache:
    """Cache for LLM responses, keyed by finding fingerprint and model."""

    def __init__(self, cache_dir: str | Path | None = None):
        """Initialize LLM cache.

        Args:
            cache_dir: Directory for cache files (default: .vibegate/llm_cache)
        """
        if cache_dir is None:
            cache_dir = Path(".vibegate/llm_cache")
        else:
            cache_dir = Path(cache_dir)

        self.cache_dir = cache_dir.resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, fingerprint: str, model: str, response_type: str) -> str:
        """Generate cache key from fingerprint, model, and response type.

        Args:
            fingerprint: Finding fingerprint (sha256:...)
            model: Model name
            response_type: Type of response (explanation, fix_prompt, combined)

        Returns:
            Cache key string
        """
        # Normalize fingerprint (remove sha256: prefix if present)
        fp = fingerprint.replace("sha256:", "")

        # Create a stable cache key
        key_input = f"{fp}_{model}_{response_type}"
        key_hash = hashlib.sha256(key_input.encode()).hexdigest()[:16]

        return f"{fp[:12]}_{key_hash}_{response_type}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file.

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def get_explanation(self, fingerprint: str, model: str) -> str | None:
        """Get cached explanation for a finding.

        Args:
            fingerprint: Finding fingerprint
            model: Model name

        Returns:
            Cached explanation or None if not found
        """
        cache_key = self._get_cache_key(fingerprint, model, "explanation")
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
                logger.debug(f"Cache hit for explanation: {fingerprint[:16]}...")
                return data.get("content")
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            return None

    def save_explanation(self, fingerprint: str, model: str, explanation: str) -> None:
        """Save explanation to cache.

        Args:
            fingerprint: Finding fingerprint
            model: Model name
            explanation: Explanation text
        """
        cache_key = self._get_cache_key(fingerprint, model, "explanation")
        cache_path = self._get_cache_path(cache_key)

        data = {
            "fingerprint": fingerprint,
            "model": model,
            "response_type": "explanation",
            "content": explanation,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached explanation for {fingerprint[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")

    def get_fix_prompt(self, fingerprint: str, model: str) -> str | None:
        """Get cached fix prompt for a finding.

        Args:
            fingerprint: Finding fingerprint
            model: Model name

        Returns:
            Cached fix prompt or None if not found
        """
        cache_key = self._get_cache_key(fingerprint, model, "fix_prompt")
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
                logger.debug(f"Cache hit for fix_prompt: {fingerprint[:16]}...")
                return data.get("content")
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            return None

    def save_fix_prompt(self, fingerprint: str, model: str, fix_prompt: str) -> None:
        """Save fix prompt to cache.

        Args:
            fingerprint: Finding fingerprint
            model: Model name
            fix_prompt: Fix prompt text
        """
        cache_key = self._get_cache_key(fingerprint, model, "fix_prompt")
        cache_path = self._get_cache_path(cache_key)

        data = {
            "fingerprint": fingerprint,
            "model": model,
            "response_type": "fix_prompt",
            "content": fix_prompt,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached fix_prompt for {fingerprint[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")

    def get_combined(self, fingerprint: str, model: str) -> dict[str, str] | None:
        """Get cached combined response (explanation + fix prompt).

        Args:
            fingerprint: Finding fingerprint
            model: Model name

        Returns:
            Dict with 'explanation' and 'fix_prompt' keys, or None if not found
        """
        cache_key = self._get_cache_key(fingerprint, model, "combined")
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
                logger.debug(f"Cache hit for combined: {fingerprint[:16]}...")
                return {
                    "explanation": data.get("explanation", ""),
                    "fix_prompt": data.get("fix_prompt", ""),
                }
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            return None

    def save_combined(
        self, fingerprint: str, model: str, explanation: str, fix_prompt: str
    ) -> None:
        """Save combined response to cache.

        Args:
            fingerprint: Finding fingerprint
            model: Model name
            explanation: Explanation text
            fix_prompt: Fix prompt text
        """
        cache_key = self._get_cache_key(fingerprint, model, "combined")
        cache_path = self._get_cache_path(cache_key)

        data = {
            "fingerprint": fingerprint,
            "model": model,
            "response_type": "combined",
            "explanation": explanation,
            "fix_prompt": fix_prompt,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached combined response for {fingerprint[:16]}...")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of cache files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats (count, total_size_bytes)
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {"count": len(cache_files), "total_size_bytes": total_size}
