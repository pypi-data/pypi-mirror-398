"""MLX backend implementation for Apple Silicon."""

import platform
from typing import Dict, Iterator, List, Optional

from .base import BackendBase, BackendInfo, GenerationParams
from ..utils.logger import get_logger

logger = get_logger()


class MLXBackend(BackendBase):
    """Backend using MLX for native Apple Silicon inference.

    MLX is optimized for M1/M2/M3 chips and provides the fastest
    inference on Apple Silicon hardware.

    Supports safetensors models from HuggingFace.
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._model_path: Optional[str] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if MLX is available (Apple Silicon + mlx installed)."""
        # Must be on macOS ARM64
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            return False

        try:
            import mlx.core
            import mlx_lm
            return True
        except ImportError:
            return False

    @classmethod
    def get_info(cls) -> BackendInfo:
        """Get MLX backend info."""
        version = "unknown"
        try:
            import mlx
            version = getattr(mlx, "__version__", "unknown")
        except ImportError:
            pass

        return BackendInfo(
            name="mlx",
            version=version,
            supports_streaming=True,
            supports_chat=True,
            model_formats=["safetensors", "mlx"]
        )

    def load_model(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,  # Ignored for MLX (always uses GPU)
        **kwargs
    ) -> None:
        """Load a model using MLX.

        Args:
            model_path: HuggingFace model ID or local path
            n_ctx: Context window size (used for generation)
            n_gpu_layers: Ignored (MLX always uses unified memory)
        """
        try:
            from mlx_lm import load
        except ImportError:
            raise ImportError(
                "mlx-lm is required for MLX backend. "
                "Install with: pip install anykernel[mlx]"
            )

        logger.info("Loading model with MLX backend...")

        self._model, self._tokenizer = load(model_path)
        self._model_path = model_path
        self._n_ctx = n_ctx

        logger.info("Model loaded successfully with MLX.")

    def generate(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> str:
        """Generate text completion."""
        self._ensure_loaded()
        params = params or GenerationParams()

        try:
            from mlx_lm import generate
        except ImportError:
            raise ImportError("mlx-lm is required for generation.")

        response = generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=params.max_tokens,
            temp=params.temperature,
            top_p=params.top_p,
            verbose=False
        )

        return response

    def generate_stream(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Generate text with streaming."""
        self._ensure_loaded()
        params = params or GenerationParams()

        try:
            from mlx_lm import stream_generate
        except ImportError:
            # Fall back to non-streaming if stream_generate not available
            yield self.generate(prompt, params)
            return

        for token in stream_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=params.max_tokens,
            temp=params.temperature,
            top_p=params.top_p
        ):
            yield token

    def chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> str:
        """Chat completion."""
        self._ensure_loaded()

        # Format messages into prompt
        prompt = self._format_chat_prompt(messages)
        return self.generate(prompt, params)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Chat completion with streaming."""
        self._ensure_loaded()

        prompt = self._format_chat_prompt(messages)
        yield from self.generate_stream(prompt, params)

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a prompt string.

        Uses ChatML format by default, but should ideally use
        the model's chat template if available.
        """
        # Try to use tokenizer's chat template if available
        if hasattr(self._tokenizer, "apply_chat_template"):
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            except Exception:
                pass

        # Fallback to simple ChatML format
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}\n"

        formatted += "<|assistant|>\n"
        return formatted

    def unload(self) -> None:
        """Unload model and free resources."""
        self._model = None
        self._tokenizer = None
        self._model_path = None

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None

    def _ensure_loaded(self):
        """Raise error if no model is loaded."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
