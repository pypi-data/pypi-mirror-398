"""Abstract base class for inference backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional


@dataclass
class BackendInfo:
    """Metadata about a backend."""
    name: str
    version: str
    supports_streaming: bool
    supports_chat: bool
    model_formats: List[str] = field(default_factory=list)  # ["gguf", "safetensors", "gptq", "exl2"]


@dataclass
class GenerationParams:
    """Parameters for text generation."""
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop: Optional[List[str]] = None


class BackendBase(ABC):
    """Abstract base class for all inference backends.

    All backends must implement this interface to be usable by AnyKernel.
    This enables seamless switching between llama.cpp, MLX, vLLM, etc.
    """

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if this backend can be used.

        Should verify:
        - Required dependencies are installed
        - Hardware requirements are met (e.g., CUDA for vLLM, Apple Silicon for MLX)

        Returns:
            True if backend is usable, False otherwise
        """
        pass

    @classmethod
    @abstractmethod
    def get_info(cls) -> BackendInfo:
        """Get backend metadata.

        Returns:
            BackendInfo with name, version, capabilities, and supported formats
        """
        pass

    @abstractmethod
    def load_model(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
        **kwargs
    ) -> None:
        """Load a model into memory.

        Args:
            model_path: Path to model file or HuggingFace model ID
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
            **kwargs: Backend-specific options
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> str:
        """Generate text completion.

        Args:
            prompt: Input text prompt
            params: Generation parameters

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Generate text with streaming output.

        Args:
            prompt: Input text prompt
            params: Generation parameters

        Yields:
            Generated tokens one at a time
        """
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> str:
        """Chat completion with message history.

        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            params: Generation parameters

        Returns:
            Assistant's response text
        """
        pass

    @abstractmethod
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Chat completion with streaming output.

        Args:
            messages: List of message dicts
            params: Generation parameters

        Yields:
            Generated tokens one at a time
        """
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model and free resources."""
        pass

    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        pass
