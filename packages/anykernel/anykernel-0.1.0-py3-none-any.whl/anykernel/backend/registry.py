"""Backend configuration registry for AnyKernel."""

from dataclasses import dataclass
from typing import Optional

from ..hardware import AcceleratorType, HardwareProfile


@dataclass
class BackendConfig:
    """Configuration for a backend."""
    name: str                       # Backend name (e.g., "cuda", "metal", "cpu")
    n_gpu_layers: int               # -1 for all layers on GPU, 0 for CPU only
    n_threads: Optional[int]        # CPU threads (None = auto)
    n_ctx: int                      # Context window size
    use_mmap: bool                  # Memory-mapped model loading
    use_mlock: bool                 # Lock memory (prevents swapping)


class BackendRegistry:
    """Registry of backend configurations for different hardware profiles."""

    # Profile configurations
    # Currently only "interactive_chat" is supported for MVP
    PROFILES = {
        "interactive_chat": {
            AcceleratorType.CUDA: BackendConfig(
                name="cuda",
                n_gpu_layers=-1,    # All layers on GPU
                n_threads=None,     # Not used for GPU
                n_ctx=4096,
                use_mmap=True,
                use_mlock=False
            ),
            AcceleratorType.METAL: BackendConfig(
                name="metal",
                n_gpu_layers=-1,    # All layers on GPU
                n_threads=None,     # Not used for GPU
                n_ctx=4096,
                use_mmap=True,
                use_mlock=False
            ),
            AcceleratorType.CPU: BackendConfig(
                name="cpu",
                n_gpu_layers=0,     # CPU only
                n_threads=None,     # Will be auto-set based on CPU cores
                n_ctx=2048,         # Smaller context for CPU
                use_mmap=True,
                use_mlock=False
            )
        }
    }

    def get_config(
        self,
        hardware: HardwareProfile,
        profile: str = "interactive_chat"
    ) -> BackendConfig:
        """Get backend configuration for hardware and profile.

        Args:
            hardware: Detected hardware profile
            profile: Inference profile name

        Returns:
            BackendConfig with optimal settings for the hardware

        Raises:
            ValueError: If profile is unknown
        """
        if profile not in self.PROFILES:
            available = ", ".join(self.PROFILES.keys())
            raise ValueError(
                f"Unknown profile: {profile}. Available profiles: {available}"
            )

        profile_configs = self.PROFILES[profile]
        config = profile_configs.get(hardware.accelerator)

        if config is None:
            # Fallback to CPU if accelerator not found
            config = profile_configs[AcceleratorType.CPU]

        # Auto-set thread count for CPU
        if config.n_threads is None and config.n_gpu_layers == 0:
            # Use all but one core, minimum 1
            n_threads = max(1, hardware.cpu_cores - 1)
            config = BackendConfig(
                name=config.name,
                n_gpu_layers=config.n_gpu_layers,
                n_threads=n_threads,
                n_ctx=config.n_ctx,
                use_mmap=config.use_mmap,
                use_mlock=config.use_mlock
            )

        return config

    def get_available_profiles(self) -> list:
        """Get list of available profile names."""
        return list(self.PROFILES.keys())
