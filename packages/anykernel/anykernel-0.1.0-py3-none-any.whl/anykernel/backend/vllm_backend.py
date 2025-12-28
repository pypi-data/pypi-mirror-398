"""vLLM backend implementation for NVIDIA GPUs."""

from typing import Dict, Iterator, List, Optional

from .base import BackendBase, BackendInfo, GenerationParams
from ..utils.logger import get_logger

logger = get_logger()


class VLLMBackend(BackendBase):
    """Backend using vLLM for high-throughput NVIDIA GPU inference.

    vLLM uses PagedAttention for efficient memory management and
    provides excellent throughput on NVIDIA GPUs.

    Supports safetensors, GPTQ, and AWQ models.
    """

    def __init__(self):
        self._llm = None
        self._model_path: Optional[str] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if vLLM is available (CUDA + vllm installed)."""
        try:
            import torch
            if not torch.cuda.is_available():
                return False

            import vllm
            return True
        except ImportError:
            return False

    @classmethod
    def get_info(cls) -> BackendInfo:
        """Get vLLM backend info."""
        version = "unknown"
        try:
            import vllm
            version = getattr(vllm, "__version__", "unknown")
        except ImportError:
            pass

        return BackendInfo(
            name="vllm",
            version=version,
            supports_streaming=True,
            supports_chat=True,
            model_formats=["safetensors", "gptq", "awq"]
        )

    def load_model(
        self,
        model_path: str,
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,  # Ignored (vLLM always uses GPU)
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        **kwargs
    ) -> None:
        """Load a model using vLLM.

        Args:
            model_path: HuggingFace model ID or local path
            n_ctx: Maximum context length
            n_gpu_layers: Ignored (vLLM requires full GPU)
            tensor_parallel_size: Number of GPUs for tensor parallelism
            gpu_memory_utilization: Fraction of GPU memory to use
        """
        try:
            from vllm import LLM
        except ImportError:
            raise ImportError(
                "vllm is required for vLLM backend. "
                "Install with: pip install anykernel[vllm]"
            )

        logger.info("Loading model with vLLM backend...")

        self._llm = LLM(
            model=model_path,
            max_model_len=n_ctx,
            tensor_parallel_size=tensor_parallel_size,
            gpu_memory_utilization=gpu_memory_utilization,
            trust_remote_code=True
        )
        self._model_path = model_path

        logger.info("Model loaded successfully with vLLM.")

    def generate(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> str:
        """Generate text completion."""
        self._ensure_loaded()
        params = params or GenerationParams()

        from vllm import SamplingParams

        sampling_params = SamplingParams(
            max_tokens=params.max_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
            top_k=params.top_k,
            repetition_penalty=params.repeat_penalty,
            stop=params.stop
        )

        outputs = self._llm.generate([prompt], sampling_params)
        return outputs[0].outputs[0].text

    def generate_stream(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None
    ) -> Iterator[str]:
        """Generate text with streaming.

        Note: vLLM streaming requires the async API. For simplicity,
        we simulate streaming by yielding the full response.
        """
        # vLLM's streaming is async-based, so we fall back to non-streaming
        # for the sync interface
        yield self.generate(prompt, params)

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
        prompt = self._format_chat_prompt(messages)
        yield from self.generate_stream(prompt, params)

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages into a prompt string.

        Uses the model's chat template if available via the tokenizer.
        """
        try:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(self._model_path)

            if hasattr(tokenizer, "apply_chat_template"):
                return tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
        except Exception:
            pass

        # Fallback to simple format
        formatted = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted += f"System: {content}\n\n"
            elif role == "user":
                formatted += f"User: {content}\n\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n\n"

        formatted += "Assistant: "
        return formatted

    def unload(self) -> None:
        """Unload model and free resources."""
        if self._llm is not None:
            del self._llm
            self._llm = None

            # Force CUDA memory cleanup
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass

        self._model_path = None

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._llm is not None

    def _ensure_loaded(self):
        """Raise error if no model is loaded."""
        if not self.is_loaded:
            raise RuntimeError("No model loaded. Call load_model() first.")
