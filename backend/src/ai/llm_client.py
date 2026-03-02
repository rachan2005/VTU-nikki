"""LLM client with automatic provider fallback chain"""
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.llm.gemini import GeminiClient
from src.core.llm.openai import OpenAIClient
from src.core.llm.cerebras import CerebrasClient
from src.core.llm.groq import GroqClient
from src.core.llm.mock import MockClient
from config import LLM_PROVIDER, LLM_MAX_RETRIES, OPENAI_API_KEY, GEMINI_API_KEY, CEREBRAS_API_KEY, GROQ_API_KEY
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Fallback order: fastest free tiers first
FALLBACK_CHAIN = ["groq", "gemini", "cerebras", "openai"]

# Errors that mean "this provider is dead, try next one"
FATAL_ERRORS = ["401", "402", "403", "invalid_api_key", "payment_required", "RESOURCE_EXHAUSTED", "quota", "rate_limit", "413"]


class LLMError(Exception):
    pass


def _is_fatal(err_str: str) -> bool:
    """Check if error means the provider is exhausted (not a transient failure)."""
    return any(code in err_str for code in FATAL_ERRORS)


class LLMClient:
    """LLM client with automatic fallback across providers.

    If provider=auto (or any configured provider fails fatally),
    it walks the chain: groq → gemini → cerebras → openai
    using whichever has a valid API key.
    """

    def __init__(self, provider: str = LLM_PROVIDER, max_retries: int = LLM_MAX_RETRIES, api_keys: Optional[Dict[str, str]] = None):
        self.max_retries = max_retries
        self.api_keys = api_keys or {}
        self.providers = self._build_chain(provider)
        self.active_idx = 0

        if not self.providers:
            raise LLMError("No LLM providers available. Set at least one API key in .env or pass api_keys")

        names = [p[0] for p in self.providers]
        logger.info(f"Initialized LLM client: {names[0]} (fallbacks: {names[1:]})")

    def _build_chain(self, primary: str) -> List[tuple]:
        """Build ordered list of (name, provider_instance) with primary first."""
        available = []

        # Resolve keys: prefer passed api_keys, fallback to env config
        groq_key = self.api_keys.get("groq_api_key") or GROQ_API_KEY
        gemini_key = self.api_keys.get("gemini_api_key") or GEMINI_API_KEY
        cerebras_key = self.api_keys.get("cerebras_api_key") or CEREBRAS_API_KEY
        openai_key = self.api_keys.get("openai_api_key") or OPENAI_API_KEY

        # Map of provider name → (api_key, factory)
        registry = {
            "groq": (groq_key, lambda: GroqClient(groq_key)),
            "gemini": (gemini_key, lambda: GeminiClient(gemini_key)),
            "cerebras": (cerebras_key, lambda: CerebrasClient(cerebras_key)),
            "openai": (openai_key, lambda: OpenAIClient(openai_key)),
        }

        # If primary is "auto", just use the fallback chain order
        if primary == "auto":
            order = FALLBACK_CHAIN
        else:
            # Primary first, then the rest as fallbacks
            order = [primary] + [p for p in FALLBACK_CHAIN if p != primary]

        for name in order:
            if name == "mock":
                available.append(("mock", MockClient()))
                continue
            entry = registry.get(name)
            if entry:
                api_key, factory = entry
                if api_key:
                    try:
                        available.append((name, factory()))
                    except Exception as e:
                        logger.warning(f"Failed to init {name}: {e}")

        return available

    @property
    def provider_name(self) -> str:
        if self.providers:
            return self.providers[self.active_idx][0]
        return "none"

    @property
    def provider(self):
        return self.providers[self.active_idx][1]

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = True
    ) -> Any:
        """Generate with automatic fallback across providers."""
        system_prompt = system or ""

        # Try each provider in the chain
        start_idx = self.active_idx
        tried = set()

        while len(tried) < len(self.providers):
            name, prov = self.providers[self.active_idx]
            tried.add(self.active_idx)

            # Retry loop for current provider
            for attempt in range(self.max_retries):
                try:
                    response = prov.generate(prompt, system_prompt)

                    if json_mode:
                        if isinstance(response, (dict, list)):
                            return response
                        elif isinstance(response, str):
                            return json.loads(response)
                        return response
                    return response

                except json.JSONDecodeError as e:
                    logger.warning(f"[{name}] Attempt {attempt + 1}: JSON parse failed: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    break  # Try next provider

                except Exception as e:
                    err_str = str(e)
                    logger.warning(f"[{name}] Attempt {attempt + 1}: {e}")

                    if _is_fatal(err_str):
                        logger.warning(f"[{name}] Fatal error, switching provider...")
                        break  # Skip remaining retries, try next provider

                    if attempt < self.max_retries - 1:
                        if "429" in err_str:
                            time.sleep(25)
                        else:
                            time.sleep(2 ** attempt)
                        continue
                    break  # Try next provider

            # Current provider exhausted — move to next
            self.active_idx = (self.active_idx + 1) % len(self.providers)
            if self.active_idx not in tried:
                next_name = self.providers[self.active_idx][0]
                logger.info(f"Falling back to: {next_name}")

        raise LLMError(
            f"All providers exhausted. Tried: {[self.providers[i][0] for i in tried]}"
        )

    def generate_bulk(self, prompts: List[str], system: Optional[str] = None, **kwargs) -> List[Any]:
        return [self.generate(prompt=p, system=system, **kwargs) for p in prompts]

    def get_stats(self) -> Dict[str, Any]:
        if hasattr(self.provider, 'get_stats'):
            return self.provider.get_stats()
        return {}


def get_llm_client(provider: Optional[str] = None, api_keys: Optional[Dict[str, str]] = None) -> LLMClient:
    """Get LLM client. Use provider='auto' for automatic fallback."""
    return LLMClient(provider=provider or LLM_PROVIDER, api_keys=api_keys)
