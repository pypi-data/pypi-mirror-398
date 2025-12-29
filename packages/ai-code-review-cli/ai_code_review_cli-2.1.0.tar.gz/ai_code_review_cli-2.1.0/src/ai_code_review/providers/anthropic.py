"""Anthropic provider implementation using LangChain."""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import SecretStr

from ai_code_review.models.config import Config
from ai_code_review.providers.base import BaseAIProvider
from ai_code_review.utils.constants import SYSTEM_PROMPT_ESTIMATED_CHARS
from ai_code_review.utils.exceptions import AIProviderError


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude AI provider implementation."""

    def __init__(self, config: Config) -> None:
        """Initialize Anthropic provider."""
        super().__init__(config)

    def _log_rate_limit_headers(self, headers: dict[str, str]) -> None:
        """Log Anthropic rate limit headers for debugging."""
        import structlog

        logger = structlog.get_logger()

        # Extract relevant rate limit headers
        rate_limit_info = {}
        for key, value in headers.items():
            if key.lower().startswith("anthropic-ratelimit-"):
                rate_limit_info[key] = value

        if rate_limit_info:
            logger.info("Anthropic rate limit status", **rate_limit_info)

    def _create_client(self) -> BaseChatModel:
        """Create ChatAnthropic client instance."""
        try:
            # Import logger here to avoid circular imports
            import structlog

            logger = structlog.get_logger()

            logger.info(
                "Creating Anthropic client",
                model=self.model_name,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
            )

            return ChatAnthropic(
                model_name=self.model_name,
                api_key=(
                    self.config.ai_api_key if self.config.ai_api_key else SecretStr("")
                ),
                temperature=self.config.temperature,
                max_tokens_to_sample=self.config.max_tokens,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
                stop=None,
            )
        except Exception as e:
            raise AIProviderError(
                f"Failed to create Anthropic client: {e}", "anthropic"
            ) from e

    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        if self.config.dry_run:
            return True

        # For cloud providers, we assume availability if we have an API key
        # Real availability check would require an actual API call
        return bool(self.config.ai_api_key)

    def get_adaptive_context_size(
        self,
        diff_size_chars: int,
        project_context_chars: int = 0,
        system_prompt_chars: int = SYSTEM_PROMPT_ESTIMATED_CHARS,
    ) -> int:
        """Get context size adaptively based on content size and config.

        Claude 3.5 Sonnet has excellent context handling:
        - Input: ~200K tokens (Claude 3.5 Sonnet)
        - Output: ~4K tokens

        We can be generous with context but not as much as Gemini.

        Args:
            diff_size_chars: Size of the diff content in characters
            project_context_chars: Size of project context content in characters
            system_prompt_chars: Estimated size of system prompt in characters

        Returns:
            Optimal context window size considering all content
        """
        # Calculate total content size
        total_content_chars = (
            diff_size_chars + project_context_chars + system_prompt_chars
        )

        # Manual override always takes precedence
        if self.config.big_diffs:
            return 200_000  # 200K - manual big-diffs flag (max context)

        # Auto-detect based on total content size (generous but not as much as Gemini)
        elif total_content_chars > 150_000:  # > 150K chars (~60K tokens)
            return 200_000  # 200K - very large content (max context)
        elif total_content_chars > 75_000:  # > 75K chars (~30K tokens)
            return 150_000  # 150K - large content
        elif total_content_chars > 30_000:  # > 30K chars (~12K tokens)
            return 100_000  # 100K - medium content
        else:
            return 64_000  # 64K - standard (still generous)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on Anthropic service.

        Note: This performs a lightweight check without making actual API calls.
        API key validation is already done by Pydantic during config initialization.
        Actual API connectivity will be verified during the first real API call.
        """
        try:
            if self.config.dry_run:
                return {
                    "status": "healthy",
                    "dry_run": True,
                    "model": self.model_name,
                    "provider": "anthropic",
                }

            # API key validation is already done by Pydantic validators in Config
            # If we reached here, the API key is present and non-empty
            # We don't make actual API calls here to avoid:
            # 1. Unnecessary API usage/costs
            # 2. Slow health checks
            # 3. Potential rate limiting
            return {
                "status": "healthy",
                "api_key_configured": True,
                "model": self.model_name,
                "provider": "anthropic",
                "note": "API key validated. Connectivity will be verified on first use.",
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "anthropic",
            }
