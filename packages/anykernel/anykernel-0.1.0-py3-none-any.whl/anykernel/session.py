"""High-level Session API for AnyKernel."""

from typing import Dict, Iterator, List, Optional, Union

from .client import AnyKernelClient
from .backend.base import BackendBase, GenerationParams
from .exceptions import SessionNotInitializedError
from .utils.logger import get_logger, set_log_level

logger = get_logger()


class Session:
    """High-level session for text generation.

    AnyKernel Session provides a simple interface for running local LLMs.
    It automatically detects hardware, downloads models, and selects
    the optimal backend (MLX, vLLM, or llama.cpp).

    Example:
        >>> from anykernel import Session
        >>>
        >>> with Session("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF") as session:
        ...     response = session.chat("Hello, how are you?")
        ...     print(response)

    Args:
        model_id: HuggingFace model ID or local path to model file
        model_file: Specific filename (optional for known models)
        backend: Backend to use ("auto", "llama_cpp", "mlx", "vllm")
        log_level: Logging level ("debug", "info", "warning", "error")
    """

    def __init__(
        self,
        model_id: str,
        model_file: Optional[str] = None,
        backend: str = "auto",
        log_level: str = "info"
    ):
        set_log_level(log_level)

        self.model_id = model_id
        self.model_file = model_file
        self.backend_name = backend

        self._client = AnyKernelClient()
        self._backend: Optional[BackendBase] = None
        self._history: List[Dict[str, str]] = []
        self._initialized = False

    def __enter__(self) -> "Session":
        """Context manager entry - load model."""
        self._backend = self._client.load_model(
            model_id=self.model_id,
            model_file=self.model_file,
            backend=self.backend_name
        )
        self._initialized = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self._client.unload()
        self._initialized = False
        return False

    def _ensure_initialized(self):
        """Ensure the session is properly initialized."""
        if not self._initialized or self._backend is None:
            raise SessionNotInitializedError(
                "Session not initialized. Use 'with Session(...) as session:' "
                "or call session.load() first."
            )

    def load(self) -> "Session":
        """Manually load the model (alternative to context manager).

        Returns:
            Self for method chaining
        """
        self._backend = self._client.load_model(
            model_id=self.model_id,
            model_file=self.model_file,
            backend=self.backend_name
        )
        self._initialized = True
        return self

    def unload(self):
        """Manually unload the model."""
        self._client.unload()
        self._initialized = False

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """Generate text from a prompt.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            stream: If True, return iterator of tokens

        Returns:
            Generated text or iterator of tokens if streaming
        """
        self._ensure_initialized()

        params = GenerationParams(
            max_tokens=max_tokens,
            temperature=temperature
        )

        if stream:
            return self._backend.generate_stream(prompt, params)
        return self._backend.generate(prompt, params)

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Union[str, Iterator[str]]:
        """Chat with conversation history.

        Args:
            message: User message
            system_prompt: Optional system prompt (used once at start)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: If True, return iterator of tokens

        Returns:
            Assistant response or iterator of tokens if streaming
        """
        self._ensure_initialized()

        # Add system prompt if provided and history is empty
        if system_prompt and not self._history:
            self._history.append({
                "role": "system",
                "content": system_prompt
            })

        # Add user message
        self._history.append({
            "role": "user",
            "content": message
        })

        params = GenerationParams(
            max_tokens=max_tokens,
            temperature=temperature
        )

        if stream:
            return self._stream_chat_response(params)

        response = self._backend.chat(self._history, params)
        self._history.append({
            "role": "assistant",
            "content": response
        })
        return response

    def _stream_chat_response(self, params: GenerationParams) -> Iterator[str]:
        """Stream chat response and store in history.

        Args:
            params: Generation parameters

        Yields:
            Generated tokens
        """
        full_response = ""
        for token in self._backend.chat_stream(self._history, params):
            full_response += token
            yield token

        # Store complete response in history
        self._history.append({
            "role": "assistant",
            "content": full_response
        })

    def clear_history(self):
        """Clear conversation history."""
        self._history = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """Get conversation history.

        Returns:
            List of message dictionaries
        """
        return self._history.copy()

    @property
    def hardware_info(self) -> dict:
        """Get detected hardware information.

        Returns:
            Dictionary with hardware details
        """
        hw = self._client.hardware
        return {
            "os": hw.os_name,
            "arch": hw.arch,
            "accelerator": hw.accelerator.value,
            "device": hw.accelerator_name,
            "cpu_cores": hw.cpu_cores,
            "is_apple_silicon": hw.is_apple_silicon
        }

    @property
    def backend_info(self) -> dict:
        """Get current backend information.

        Returns:
            Dictionary with backend details
        """
        if self._backend is None:
            return {"name": None, "loaded": False}

        info = self._backend.get_info()
        return {
            "name": info.name,
            "version": info.version,
            "supports_streaming": info.supports_streaming,
            "supports_chat": info.supports_chat,
            "model_formats": info.model_formats,
            "loaded": self._backend.is_loaded
        }

    def list_available_backends(self) -> list:
        """List all available backends.

        Returns:
            List of backend info dictionaries
        """
        backends = self._client.list_available_backends()
        return [
            {
                "name": b.name,
                "version": b.version,
                "model_formats": b.model_formats
            }
            for b in backends
        ]
