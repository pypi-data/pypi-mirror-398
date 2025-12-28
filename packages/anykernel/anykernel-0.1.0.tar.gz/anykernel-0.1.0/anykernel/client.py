"""Internal client for AnyKernel."""

from typing import Optional

from .backend.base import BackendBase
from .backend.selector import BackendSelector, detect_model_format
from .hardware import HardwareDetector, HardwareProfile
from .utils.cache import ModelCache
from .utils.logger import get_logger

logger = get_logger()


class AnyKernelClient:
    """Internal client coordinating hardware, backend, and model.

    This client handles:
    - Hardware detection
    - Backend selection (MLX, vLLM, llama.cpp)
    - Model loading and caching
    """

    def __init__(self):
        self.detector = HardwareDetector()
        self.selector = BackendSelector()
        self.cache = ModelCache()
        self._hardware: Optional[HardwareProfile] = None
        self._backend: Optional[BackendBase] = None

    @property
    def hardware(self) -> HardwareProfile:
        """Lazy hardware detection.

        Returns:
            Detected hardware profile
        """
        if self._hardware is None:
            self._hardware = self.detector.detect()
        return self._hardware

    @property
    def backend(self) -> Optional[BackendBase]:
        """Get current backend."""
        return self._backend

    def load_model(
        self,
        model_id: str,
        model_file: Optional[str] = None,
        backend: str = "auto",
        n_ctx: int = 2048,
        n_gpu_layers: int = -1,
        **kwargs
    ) -> BackendBase:
        """Load model with automatic backend selection.

        Args:
            model_id: HuggingFace model ID or local path
            model_file: Specific model filename (for GGUF)
            backend: Backend to use ("auto", "llama_cpp", "mlx", "vllm")
            n_ctx: Context window size
            n_gpu_layers: GPU layers (-1 = all, 0 = CPU)
            **kwargs: Additional backend-specific options

        Returns:
            Loaded backend instance
        """
        # Resolve model path (download if needed)
        model_path = self.cache.get_model_path(model_id, model_file)

        # Detect model format
        model_format = detect_model_format(model_path)
        logger.info(f"Model format: {model_format}")

        # Select backend
        if backend == "auto":
            self._backend = self.selector.select(
                hardware=self.hardware,
                model_format=model_format
            )
        else:
            self._backend = self.selector._get_specific_backend(
                backend_name=backend,
                model_format=model_format
            )

        # Load model
        self._backend.load_model(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            **kwargs
        )

        return self._backend

    def get_backend(self) -> BackendBase:
        """Get current backend.

        Returns:
            Current backend instance

        Raises:
            RuntimeError: If no model is loaded
        """
        if self._backend is None:
            raise RuntimeError("No model loaded. Call load_model() first.")
        return self._backend

    def unload(self):
        """Unload current model and free resources."""
        if self._backend is not None:
            self._backend.unload()
            self._backend = None

    def list_available_backends(self) -> list:
        """List all available backends.

        Returns:
            List of BackendInfo for available backends
        """
        return self.selector.get_available_backends()
