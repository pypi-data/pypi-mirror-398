"""Model runner for AnyKernel."""

from dataclasses import dataclass, field
from typing import Iterator, List, Dict, Optional


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop: Optional[List[str]] = field(default=None)


class ModelRunner:
    """Wraps a loaded model with generation utilities."""

    DEFAULT_CONFIG = GenerationConfig()

    def __init__(self, model):
        """Initialize the runner with a loaded model.

        Args:
            model: Loaded Llama model instance
        """
        self.model = model

    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Generate text completion.

        Args:
            prompt: Input text prompt
            config: Generation configuration

        Returns:
            Generated text
        """
        config = config or self.DEFAULT_CONFIG

        output = self.model(
            prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repeat_penalty,
            stop=config.stop
        )

        return output["choices"][0]["text"]

    def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> Iterator[str]:
        """Generate text with streaming output.

        Args:
            prompt: Input text prompt
            config: Generation configuration

        Yields:
            Generated tokens one at a time
        """
        config = config or self.DEFAULT_CONFIG

        for chunk in self.model(
            prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repeat_penalty,
            stop=config.stop,
            stream=True
        ):
            yield chunk["choices"][0]["text"]

    def chat(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> str:
        """Chat completion with message history.

        Args:
            messages: List of message dicts with "role" and "content"
            config: Generation configuration

        Returns:
            Assistant's response text
        """
        config = config or self.DEFAULT_CONFIG

        response = self.model.create_chat_completion(
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repeat_penalty,
            stop=config.stop
        )

        return response["choices"][0]["message"]["content"]

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        config: Optional[GenerationConfig] = None
    ) -> Iterator[str]:
        """Chat completion with streaming output.

        Args:
            messages: List of message dicts with "role" and "content"
            config: Generation configuration

        Yields:
            Generated tokens one at a time
        """
        config = config or self.DEFAULT_CONFIG

        for chunk in self.model.create_chat_completion(
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            repeat_penalty=config.repeat_penalty,
            stop=config.stop,
            stream=True
        ):
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                yield delta["content"]
