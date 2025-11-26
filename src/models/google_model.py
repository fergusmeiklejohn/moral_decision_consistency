"""
Google model provider implementation.

Supports Gemini 1.5 Pro, Gemini 1.5 Flash, and other Google models.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import time

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from .base import BaseLLMProvider
from ..data.schemas import ModelResponse


class GoogleProvider(BaseLLMProvider):
    """Provider for Google Gemini models."""

    def _initialize(self) -> None:
        """Initialize Google Generative AI client."""
        if not GOOGLE_AVAILABLE:
            raise ImportError(
                "Google Generative AI library not installed. "
                "Install with: pip install google-generativeai"
            )

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        top_p: float = 1.0,
        max_tokens: int = 500,
        seed: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate a response using Google Gemini API.

        Args:
            prompt: The input prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            seed: Random seed (not supported by Google, ignored)
            **kwargs: Additional Google-specific parameters

        Returns:
            ModelResponse object
        """
        start_time = time.time()

        # Build generation config
        generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "max_output_tokens": max_tokens,
        }

        # Add any additional parameters
        generation_config.update(kwargs)

        # Note: Google doesn't support seed parameter
        if seed is not None:
            print(f"Warning: Random seed {seed} specified but not supported by Google")

        # Make API call
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            response_time = time.time() - start_time

            # Extract response
            raw_text = response.text
            finish_reason = response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN"

            # Token accounting (best effort from available metadata)
            usage = getattr(response, "usage_metadata", None)
            tokens_used = getattr(usage, "total_token_count", None) if usage else None
            input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
            # Candidates token count is a reasonable proxy for output tokens
            output_tokens = getattr(usage, "candidates_token_count", None) if usage else None

            # Parse choice and reasoning
            parsed_choice, reasoning = self._parse_response(raw_text)

            return ModelResponse(
                raw_text=raw_text,
                parsed_choice=parsed_choice,
                reasoning=reasoning,
                timestamp=datetime.utcnow(),
                response_time_seconds=response_time,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                finish_reason=finish_reason
            )

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = f"Google API error: {str(e)}"

            return ModelResponse(
                raw_text=error_msg,
                parsed_choice="ERROR",
                reasoning=error_msg,
                timestamp=datetime.utcnow(),
                response_time_seconds=response_time,
                tokens_used=0,
                finish_reason="error"
            )

    def get_model_info(self) -> Dict[str, Any]:
        """Get Google model information."""
        return {
            "provider": "google",
            "model_name": self.model_name,
            "supports_seed": False,
            "supports_temperature": True,
            "note": "Google Gemini models do not support random seeds for reproducibility"
        }
