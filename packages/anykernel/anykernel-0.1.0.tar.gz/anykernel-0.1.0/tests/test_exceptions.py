"""Tests for exception classes."""

import pytest

from anykernel.exceptions import (
    AnyKernelError,
    HardwareDetectionError,
    ModelNotFoundError,
    ModelDownloadError,
    BackendLoadError,
    BackendNotAvailableError,
    GenerationError,
    SessionNotInitializedError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_exceptions_inherit_from_anykernel_error(self):
        """All custom exceptions should inherit from AnyKernelError."""
        exceptions = [
            HardwareDetectionError,
            ModelNotFoundError,
            ModelDownloadError,
            BackendLoadError,
            BackendNotAvailableError,
            GenerationError,
            SessionNotInitializedError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, AnyKernelError)

    def test_anykernel_error_inherits_from_exception(self):
        """Base AnyKernelError should inherit from Exception."""
        assert issubclass(AnyKernelError, Exception)


class TestExceptionInstantiation:
    """Tests for exception instantiation and messages."""

    def test_anykernel_error_with_message(self):
        error = AnyKernelError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_hardware_detection_error(self):
        error = HardwareDetectionError("Failed to detect GPU")
        assert str(error) == "Failed to detect GPU"
        assert isinstance(error, AnyKernelError)

    def test_model_not_found_error(self):
        error = ModelNotFoundError("Model file not found: /path/to/model.gguf")
        assert "Model file not found" in str(error)
        assert isinstance(error, AnyKernelError)

    def test_model_download_error(self):
        error = ModelDownloadError("Network error during download")
        assert "Network error" in str(error)
        assert isinstance(error, AnyKernelError)

    def test_backend_load_error(self):
        error = BackendLoadError("Failed to initialize CUDA")
        assert "CUDA" in str(error)
        assert isinstance(error, AnyKernelError)

    def test_backend_not_available_error(self):
        error = BackendNotAvailableError("MLX requires Apple Silicon")
        assert "MLX" in str(error)
        assert isinstance(error, AnyKernelError)

    def test_generation_error(self):
        error = GenerationError("Out of memory during generation")
        assert "Out of memory" in str(error)
        assert isinstance(error, AnyKernelError)

    def test_session_not_initialized_error(self):
        error = SessionNotInitializedError("Session not initialized")
        assert "not initialized" in str(error)
        assert isinstance(error, AnyKernelError)


class TestExceptionCatching:
    """Tests for catching exceptions."""

    def test_catch_specific_exception(self):
        """Test catching a specific exception type."""
        with pytest.raises(ModelNotFoundError):
            raise ModelNotFoundError("Not found")

    def test_catch_base_exception(self):
        """Test catching via base AnyKernelError."""
        with pytest.raises(AnyKernelError):
            raise BackendLoadError("Load failed")

    def test_catch_as_standard_exception(self):
        """Test catching via standard Exception."""
        with pytest.raises(Exception):
            raise GenerationError("Generation failed")
