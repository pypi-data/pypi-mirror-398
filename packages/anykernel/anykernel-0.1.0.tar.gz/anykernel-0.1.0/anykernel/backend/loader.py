"""Backend loader for AnyKernel."""

from typing import Optional

from ..exceptions import BackendLoadError
from ..hardware import AcceleratorType, HardwareProfile
from ..utils.cache import ModelCache
from ..utils.logger import get_logger
from .registry import BackendRegistry


class BackendLoader:
    """Loads llama-cpp-python backend with appropriate configuration."""

    def __init__(self):
        self.registry = BackendRegistry()
        self.cache = ModelCache()
        self.logger = get_logger()

    def load(
        self,
        model_id: str,
        hardware: HardwareProfile,
        profile: str = "interactive_chat",
        model_file: Optional[str] = None
    ):
        """Load model with optimal backend configuration.

        Args:
            model_id: HuggingFace model ID or local path
            hardware: Detected hardware profile
            profile: Inference profile name
            model_file: Specific GGUF filename (optional)

        Returns:
            Loaded Llama model instance

        Raises:
            BackendLoadError: If model loading fails
        """
        config = self.registry.get_config(hardware, profile)

        self.logger.info(f"Profile: {profile}")
        self.logger.info(f"Selecting backend: llama.cpp + {config.name.title()}")

        # Resolve model path (download if needed)
        model_path = self.cache.get_model_path(model_id, model_file)

        try:
            from llama_cpp import Llama
        except ImportError:
            raise BackendLoadError(
                "llama-cpp-python is required. "
                "Install with: pip install llama-cpp-python"
            )

        try:
            self.logger.info("Loading model...")

            llm = Llama(
                model_path=model_path,
                n_gpu_layers=config.n_gpu_layers,
                n_threads=config.n_threads,
                n_ctx=config.n_ctx,
                use_mmap=config.use_mmap,
                use_mlock=config.use_mlock,
                verbose=False  # We handle our own logging
            )

            self.logger.info("Ready.")
            return llm

        except Exception as e:
            error_msg = str(e).lower()

            # Check for GPU-related errors and fallback to CPU
            gpu_errors = ["cuda", "metal", "gpu", "out of memory", "vram"]
            is_gpu_error = any(err in error_msg for err in gpu_errors)

            if is_gpu_error and config.n_gpu_layers != 0:
                self.logger.warning(f"GPU backend failed: {e}")
                self.logger.warning("Falling back to CPU backend...")

                return self._load_cpu_fallback(model_path, hardware, profile)

            raise BackendLoadError(f"Failed to load model: {e}")

    def _load_cpu_fallback(
        self,
        model_path: str,
        hardware: HardwareProfile,
        profile: str
    ):
        """Load model with CPU fallback configuration.

        Args:
            model_path: Path to the model file
            hardware: Hardware profile
            profile: Profile name

        Returns:
            Loaded Llama model with CPU configuration
        """
        from llama_cpp import Llama

        # Get CPU configuration
        cpu_config = self.registry.PROFILES[profile][AcceleratorType.CPU]
        n_threads = cpu_config.n_threads or max(1, hardware.cpu_cores - 1)

        try:
            llm = Llama(
                model_path=model_path,
                n_gpu_layers=0,  # Force CPU
                n_threads=n_threads,
                n_ctx=cpu_config.n_ctx,
                use_mmap=True,
                verbose=False
            )

            self.logger.info("Loaded with CPU backend.")
            return llm

        except Exception as e:
            raise BackendLoadError(f"CPU fallback also failed: {e}")
