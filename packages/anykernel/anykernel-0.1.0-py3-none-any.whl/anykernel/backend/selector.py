"""Backend selector for automatic backend selection."""

from typing import Dict, List, Optional, Type

from .base import BackendBase, BackendInfo
from .llama_cpp import LlamaCppBackend
from .mlx_backend import MLXBackend
from .vllm_backend import VLLMBackend
from ..hardware import AcceleratorType, HardwareProfile
from ..exceptions import BackendNotAvailableError
from ..utils.logger import get_logger

logger = get_logger()


# Registry of all known backends
BACKEND_REGISTRY: Dict[str, Type[BackendBase]] = {
    "llama_cpp": LlamaCppBackend,
    "mlx": MLXBackend,
    "vllm": VLLMBackend,
}

# Priority order for each accelerator type
# First available backend in the list will be used
BACKEND_PRIORITY: Dict[AcceleratorType, List[str]] = {
    AcceleratorType.METAL: ["mlx", "llama_cpp"],
    AcceleratorType.CUDA: ["vllm", "llama_cpp"],
    AcceleratorType.CPU: ["llama_cpp"],
}

# Model format to backend mapping
FORMAT_BACKENDS: Dict[str, List[str]] = {
    "gguf": ["llama_cpp"],
    "safetensors": ["mlx", "vllm", "llama_cpp"],
    "gptq": ["vllm"],
    "awq": ["vllm"],
    "exl2": [],  # ExLlama not implemented yet
}


class BackendSelector:
    """Selects the best available backend for the given hardware and model."""

    def __init__(self):
        self._cache: Dict[str, bool] = {}

    def get_available_backends(self) -> List[BackendInfo]:
        """Get list of all available backends.

        Returns:
            List of BackendInfo for backends that are installed and usable
        """
        available = []
        for name, cls in BACKEND_REGISTRY.items():
            if self._is_backend_available(name, cls):
                available.append(cls.get_info())
        return available

    def select(
        self,
        hardware: HardwareProfile,
        model_format: str = "gguf",
        preferred_backend: Optional[str] = None
    ) -> BackendBase:
        """Select the best backend for the given hardware and model format.

        Args:
            hardware: Detected hardware profile
            model_format: Model format (gguf, safetensors, gptq, etc.)
            preferred_backend: Optional specific backend to use

        Returns:
            Instantiated backend ready for use

        Raises:
            BackendNotAvailableError: If no suitable backend is found
        """
        # If user specified a backend, try to use it
        if preferred_backend:
            return self._get_specific_backend(preferred_backend, model_format)

        # Get priority list for this hardware
        priorities = BACKEND_PRIORITY.get(
            hardware.accelerator,
            ["llama_cpp"]  # Fallback to llama.cpp
        )

        # Get backends that support this model format
        format_backends = set(FORMAT_BACKENDS.get(model_format, []))

        # Find first available backend that supports the format
        for backend_name in priorities:
            if backend_name not in format_backends:
                continue

            cls = BACKEND_REGISTRY.get(backend_name)
            if cls and self._is_backend_available(backend_name, cls):
                logger.info(f"Selected backend: {cls.get_info().name}")
                return cls()

        # If no format-specific backend found, try any available backend
        for backend_name in priorities:
            cls = BACKEND_REGISTRY.get(backend_name)
            if cls and self._is_backend_available(backend_name, cls):
                info = cls.get_info()
                if model_format in info.model_formats:
                    logger.info(f"Selected backend: {info.name}")
                    return cls()

        # Last resort: any available backend
        for name, cls in BACKEND_REGISTRY.items():
            if self._is_backend_available(name, cls):
                info = cls.get_info()
                if model_format in info.model_formats:
                    logger.warning(
                        f"Using fallback backend: {info.name}"
                    )
                    return cls()

        raise BackendNotAvailableError(
            f"No backend available for format '{model_format}' on {hardware.accelerator.value}.\n"
            f"Install a backend: pip install anykernel[llama]"
        )

    def _get_specific_backend(
        self,
        backend_name: str,
        model_format: str
    ) -> BackendBase:
        """Get a specific backend by name.

        Args:
            backend_name: Backend name (llama_cpp, mlx, vllm)
            model_format: Model format to validate

        Returns:
            Instantiated backend

        Raises:
            BackendNotAvailableError: If backend unavailable or incompatible
        """
        cls = BACKEND_REGISTRY.get(backend_name)
        if cls is None:
            available = ", ".join(BACKEND_REGISTRY.keys())
            raise BackendNotAvailableError(
                f"Unknown backend: {backend_name}. Available: {available}"
            )

        if not self._is_backend_available(backend_name, cls):
            raise BackendNotAvailableError(
                f"Backend '{backend_name}' is not available. "
                f"Install with: pip install anykernel[{backend_name.replace('_', '')}]"
            )

        info = cls.get_info()
        if model_format not in info.model_formats:
            raise BackendNotAvailableError(
                f"Backend '{backend_name}' does not support '{model_format}' format. "
                f"Supported formats: {', '.join(info.model_formats)}"
            )

        return cls()

    def _is_backend_available(
        self,
        name: str,
        cls: Type[BackendBase]
    ) -> bool:
        """Check if a backend is available, with caching."""
        if name not in self._cache:
            try:
                self._cache[name] = cls.is_available()
            except Exception:
                self._cache[name] = False

        return self._cache[name]


def detect_model_format(model_path: str) -> str:
    """Detect the format of a model from its path.

    Args:
        model_path: Path to model file or HuggingFace model ID

    Returns:
        Model format string (gguf, safetensors, gptq, etc.)
    """
    path_lower = model_path.lower()

    # Check file extension
    if path_lower.endswith(".gguf"):
        return "gguf"

    # Check for format indicators in path/name
    if "gguf" in path_lower:
        return "gguf"
    if "gptq" in path_lower:
        return "gptq"
    if "awq" in path_lower:
        return "awq"
    if "exl2" in path_lower:
        return "exl2"

    # Default to safetensors (most HuggingFace models)
    return "safetensors"
