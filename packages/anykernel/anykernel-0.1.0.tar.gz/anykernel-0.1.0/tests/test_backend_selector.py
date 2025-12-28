"""Tests for backend selection module."""

from unittest.mock import patch, MagicMock

import pytest

from anykernel.backend.base import BackendBase, BackendInfo, GenerationParams
from anykernel.backend.selector import (
    BackendSelector,
    detect_model_format,
    BACKEND_REGISTRY,
    BACKEND_PRIORITY,
    FORMAT_BACKENDS,
)
from anykernel.hardware import HardwareProfile, AcceleratorType
from anykernel.exceptions import BackendNotAvailableError


class TestGenerationParams:
    """Tests for GenerationParams dataclass."""

    def test_default_values(self):
        params = GenerationParams()
        assert params.max_tokens == 512
        assert params.temperature == 0.7
        assert params.top_p == 0.95
        assert params.top_k == 40
        assert params.repeat_penalty == 1.1
        assert params.stop is None

    def test_custom_values(self):
        params = GenerationParams(
            max_tokens=256,
            temperature=0.5,
            stop=["END"]
        )
        assert params.max_tokens == 256
        assert params.temperature == 0.5
        assert params.stop == ["END"]


class TestBackendInfo:
    """Tests for BackendInfo dataclass."""

    def test_create_backend_info(self):
        info = BackendInfo(
            name="test_backend",
            version="1.0.0",
            supports_streaming=True,
            supports_chat=True,
            model_formats=["gguf", "safetensors"]
        )
        assert info.name == "test_backend"
        assert info.version == "1.0.0"
        assert info.supports_streaming is True
        assert "gguf" in info.model_formats


class TestBackendRegistry:
    """Tests for the backend registry."""

    def test_registry_contains_llama_cpp(self):
        assert "llama_cpp" in BACKEND_REGISTRY

    def test_registry_contains_mlx(self):
        assert "mlx" in BACKEND_REGISTRY

    def test_registry_contains_vllm(self):
        assert "vllm" in BACKEND_REGISTRY


class TestBackendPriority:
    """Tests for backend priority configuration."""

    def test_metal_priority_prefers_mlx(self):
        priorities = BACKEND_PRIORITY[AcceleratorType.METAL]
        assert priorities[0] == "mlx"
        assert "llama_cpp" in priorities

    def test_cuda_priority_prefers_vllm(self):
        priorities = BACKEND_PRIORITY[AcceleratorType.CUDA]
        assert priorities[0] == "vllm"
        assert "llama_cpp" in priorities

    def test_cpu_has_llama_cpp(self):
        priorities = BACKEND_PRIORITY[AcceleratorType.CPU]
        assert "llama_cpp" in priorities


class TestDetectModelFormat:
    """Tests for model format detection."""

    def test_detect_gguf_extension(self):
        assert detect_model_format("model.gguf") == "gguf"
        assert detect_model_format("/path/to/model.GGUF") == "gguf"

    def test_detect_gguf_in_name(self):
        assert detect_model_format("TheBloke/Model-GGUF") == "gguf"

    def test_detect_gptq_in_name(self):
        assert detect_model_format("TheBloke/Model-GPTQ") == "gptq"

    def test_detect_awq_in_name(self):
        assert detect_model_format("TheBloke/Model-AWQ") == "awq"

    def test_detect_exl2_in_name(self):
        assert detect_model_format("SomeModel-exl2") == "exl2"

    def test_default_to_safetensors(self):
        assert detect_model_format("meta-llama/Llama-2-7b") == "safetensors"
        assert detect_model_format("some/model") == "safetensors"


class TestBackendSelector:
    """Tests for BackendSelector class."""

    def test_get_available_backends_returns_list(self):
        selector = BackendSelector()
        backends = selector.get_available_backends()

        assert isinstance(backends, list)
        # Should return list of BackendInfo objects
        for info in backends:
            assert isinstance(info, BackendInfo)

    @patch.object(BACKEND_REGISTRY["llama_cpp"], "is_available", return_value=True)
    def test_select_llama_cpp_for_cpu(self, mock_available):
        selector = BackendSelector()
        selector._cache.clear()  # Clear cache

        profile = HardwareProfile(
            os_name="Linux",
            arch="x86_64",
            cpu_cores=8,
            cpu_features=[],
            accelerator=AcceleratorType.CPU,
            accelerator_name="Intel",
            vram_mb=None,
            is_apple_silicon=False
        )

        backend = selector.select(profile, model_format="gguf")
        assert backend is not None

    def test_raises_error_when_no_backend_available(self):
        selector = BackendSelector()

        # Mock all backends as unavailable
        with patch.object(BACKEND_REGISTRY["llama_cpp"], "is_available", return_value=False), \
             patch.object(BACKEND_REGISTRY["mlx"], "is_available", return_value=False), \
             patch.object(BACKEND_REGISTRY["vllm"], "is_available", return_value=False):

            selector._cache.clear()

            profile = HardwareProfile(
                os_name="Linux",
                arch="x86_64",
                cpu_cores=8,
                cpu_features=[],
                accelerator=AcceleratorType.CPU,
                accelerator_name="Intel",
                vram_mb=None,
                is_apple_silicon=False
            )

            with pytest.raises(BackendNotAvailableError):
                selector.select(profile, model_format="gguf")

    def test_get_specific_backend_unknown(self):
        selector = BackendSelector()

        with pytest.raises(BackendNotAvailableError) as exc_info:
            selector._get_specific_backend("unknown_backend", "gguf")

        assert "Unknown backend" in str(exc_info.value)

    @patch.object(BACKEND_REGISTRY["llama_cpp"], "is_available", return_value=True)
    def test_get_specific_backend_format_mismatch(self, mock_available):
        selector = BackendSelector()
        selector._cache.clear()

        # llama.cpp only supports gguf, not gptq
        with pytest.raises(BackendNotAvailableError) as exc_info:
            selector._get_specific_backend("llama_cpp", "gptq")

        assert "does not support" in str(exc_info.value)


class TestFormatBackends:
    """Tests for format-to-backend mapping."""

    def test_gguf_maps_to_llama_cpp(self):
        assert "llama_cpp" in FORMAT_BACKENDS["gguf"]

    def test_safetensors_maps_to_multiple(self):
        backends = FORMAT_BACKENDS["safetensors"]
        assert "mlx" in backends
        assert "vllm" in backends

    def test_gptq_maps_to_vllm(self):
        assert "vllm" in FORMAT_BACKENDS["gptq"]
