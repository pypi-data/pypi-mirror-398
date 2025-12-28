"""Backend module for AnyKernel.

Provides multiple inference backend implementations:
- llama.cpp (CPU, CUDA, Metal) - Universal fallback
- MLX (Apple Silicon) - Fastest on M1/M2/M3
- vLLM (NVIDIA GPU) - High throughput serving
"""

from .base import BackendBase, BackendInfo, GenerationParams
from .selector import BackendSelector, detect_model_format, BACKEND_REGISTRY
from .llama_cpp import LlamaCppBackend
from .mlx_backend import MLXBackend
from .vllm_backend import VLLMBackend
from .registry import BackendConfig, BackendRegistry
from .loader import BackendLoader

__all__ = [
    # Base classes
    "BackendBase",
    "BackendInfo",
    "GenerationParams",
    # Selector
    "BackendSelector",
    "detect_model_format",
    "BACKEND_REGISTRY",
    # Backends
    "LlamaCppBackend",
    "MLXBackend",
    "VLLMBackend",
    # Legacy (for compatibility)
    "BackendConfig",
    "BackendRegistry",
    "BackendLoader",
]
