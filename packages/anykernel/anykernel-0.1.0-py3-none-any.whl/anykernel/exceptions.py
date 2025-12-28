"""Custom exceptions for AnyKernel."""


class AnyKernelError(Exception):
    """Base exception for AnyKernel."""
    pass


class HardwareDetectionError(AnyKernelError):
    """Failed to detect hardware capabilities."""
    pass


class ModelNotFoundError(AnyKernelError):
    """Model file not found locally or remotely."""
    pass


class ModelDownloadError(AnyKernelError):
    """Failed to download model from remote source."""
    pass


class BackendLoadError(AnyKernelError):
    """Failed to load inference backend."""
    pass


class BackendNotAvailableError(AnyKernelError):
    """Requested backend is not available on this system."""
    pass


class GenerationError(AnyKernelError):
    """Error during text generation."""
    pass


class SessionNotInitializedError(AnyKernelError):
    """Session was not properly initialized."""
    pass
