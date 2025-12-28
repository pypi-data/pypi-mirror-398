"""
AnyKernel - Zero-config inference OS for local LLMs.

AnyKernel automatically detects your hardware and loads the optimal
inference backend, so you can focus on building applications instead
of configuring CUDA, Metal, or CPU threading.

Example:
    >>> from anykernel import Session
    >>>
    >>> with Session("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF") as session:
    ...     print(session.hardware_info)
    ...     response = session.chat("What is the capital of France?")
    ...     print(response)
"""

from .session import Session
from .hardware import (
    HardwareDetector,
    HardwareProfile,
    AcceleratorType,
    detect_hardware,
)
from .backend.base import GenerationParams
from .model.runner import GenerationConfig  # Legacy alias
from .utils.cache import ModelCache
from .utils.logger import set_log_level
from .exceptions import (
    AnyKernelError,
    HardwareDetectionError,
    ModelNotFoundError,
    ModelDownloadError,
    BackendLoadError,
    BackendNotAvailableError,
    GenerationError,
    SessionNotInitializedError,
)

__version__ = "0.1.0"

__all__ = [
    # Main API
    "Session",
    # Hardware
    "HardwareDetector",
    "HardwareProfile",
    "AcceleratorType",
    "detect_hardware",
    # Configuration
    "GenerationParams",
    "GenerationConfig",  # Legacy alias
    # Utilities
    "ModelCache",
    "set_log_level",
    # Exceptions
    "AnyKernelError",
    "HardwareDetectionError",
    "ModelNotFoundError",
    "ModelDownloadError",
    "BackendLoadError",
    "BackendNotAvailableError",
    "GenerationError",
    "SessionNotInitializedError",
]
