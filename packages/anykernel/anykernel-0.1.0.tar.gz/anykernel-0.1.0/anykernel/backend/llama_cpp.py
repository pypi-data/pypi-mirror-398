"""llama.cpp backend implementation using llama-cpp-python."""

from typing import Dict, Iterator, List, Optional

from .base import BackendBase, BackendInfo, GenerationParams
from ..utils.logger import get_logger

logger = get_logger()


class LlamaCppBackend(BackendBase):
    """Backend using llama-cpp-python for inference.

    Supports GGUF models on CPU, CUDA, and Metal.
    This is the universal fallback backend that works on all platforms.
    """

    def __init__(self):
        self._model = None
        self._model_path: Optional[str] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if llama-cpp-python is installed."""
        try:
            import llama_cpp
            return True
        except ImportError:
            return False

    @classmethod
    def get_info(cls) -> BackendInfo:
        """Get llama.cpp backend info."""
        version = "unknown"
        try:
            import llama_cpp
            version = getattr(llama_cpp, "__version__", "unknown")
        except ImportError:
            pass

        return BackendInfo(
            name="llama.cpp",
            version=version,
            supports_streaming=True,
            supports_chat=True,
            model_formats=["gguf"]
        )

    def load_model(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
        n_threads: Optional[int] = None,
        use_mmap: bool = True,
        use_mlock: bool = False,
        **kwargs
    ) -> None:
        """Load a GGUF model.

        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_gpu_layers: GPU layers (-1 = all, 0 = CPU only)
            n_threads: CPU threads (None = auto)
            use_mmap: Use memory-mapped loading
            use_mlock: Lock memory to prevent swapping
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python is required. "
                "Install with: pip install anykernel[llama]"
            )

        logger.info("Loading model with llama.cpp backend...")

        self._model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            n_threads=n_threads,
            use_mmap=use_mmap,
            use_mlock=use_mlock,
            verbose=False
        )
        self._model_path = model_path
        logger.info("Model loaded successfully.")

    def generate(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> str:
        """Generate text completion."""
        self._ensure_loaded()
        params = params or GenerationParams()

        output = self._model(
            prompt,
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            repeat_penalty=params.repeat_penalty,
            stop=params.stop
        )

        return output["choices"][0]["text"]

    def generate_stream(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Generate text with streaming."""
        self._ensure_loaded()
        params = params or GenerationParams()

        for chunk in self._model(
            prompt,
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            repeat_penalty=params.repeat_penalty,
            stop=params.stop,
            stream=True
        ):
            yield chunk["choices"][0]["text"]

    def chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> str:
        """Chat completion."""
        self._ensure_loaded()
        params = params or GenerationParams()

        response = self._model.create_chat_completion(
            messages=messages,
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            repeat_penalty=params.repeat_penalty,
            stop=params.stop
        )

        return response["choices"][0]["message"]["content"]

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Chat completion with streaming."""
        self._ensure_loaded()
        params = params or GenerationParams()

        for chunk in self._model.create_chat_completion(
            messages=messages,
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            repeat_penalty=params.repeat_penalty,
            stop=params.stop,
            stream=True
        ):
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                yield delta["content"]

    def unload(self) -> None:
        """Unload model and free resources."""
        self._model = None
        self._model_path = None

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def _ensure_loaded(self):
        """Raise error if no model is loaded."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
