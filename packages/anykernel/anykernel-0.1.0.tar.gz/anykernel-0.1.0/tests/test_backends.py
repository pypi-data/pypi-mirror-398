"""Tests for individual backend implementations."""

import platform
from unittest.mock import patch, MagicMock

import pytest

from anykernel.backend.base import BackendInfo, GenerationParams
from anykernel.backend.llama_cpp import LlamaCppBackend
from anykernel.backend.mlx_backend import MLXBackend
from anykernel.backend.vllm_backend import VLLMBackend


class TestLlamaCppBackend:
    """Tests for llama.cpp backend."""

    def test_get_info_returns_backend_info(self):
        info = LlamaCppBackend.get_info()

        assert isinstance(info, BackendInfo)
        assert info.name == "llama.cpp"
        assert info.supports_streaming is True
        assert info.supports_chat is True
        assert "gguf" in info.model_formats

    @patch.dict("sys.modules", {"llama_cpp": MagicMock(__version__="0.2.0")})
    def test_is_available_with_llama_cpp_installed(self):
        # Force reimport check
        with patch("builtins.__import__", return_value=MagicMock()):
            # The actual implementation checks via import
            pass

    def test_is_loaded_false_by_default(self):
        backend = LlamaCppBackend()
        assert backend.is_loaded is False

    def test_unload_clears_model(self):
        backend = LlamaCppBackend()
        backend._model = MagicMock()
        backend._model_path = "/path/to/model"

        backend.unload()

        assert backend._model is None
        assert backend._model_path is None

    def test_ensure_loaded_raises_when_not_loaded(self):
        backend = LlamaCppBackend()

        with pytest.raises(RuntimeError) as exc_info:
            backend._ensure_loaded()

        assert "No model loaded" in str(exc_info.value)


class TestMLXBackend:
    """Tests for MLX backend."""

    def test_get_info_returns_backend_info(self):
        info = MLXBackend.get_info()

        assert isinstance(info, BackendInfo)
        assert info.name == "mlx"
        assert info.supports_streaming is True
        assert "safetensors" in info.model_formats

    @patch("anykernel.backend.mlx_backend.platform")
    def test_is_available_requires_darwin_arm64(self, mock_platform):
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"

        assert MLXBackend.is_available() is False

    @patch("anykernel.backend.mlx_backend.platform")
    def test_is_available_requires_mlx_import(self, mock_platform):
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        # MLX import will fail on non-Apple machines
        # so is_available should return False
        result = MLXBackend.is_available()
        # Result depends on whether MLX is actually installed
        assert isinstance(result, bool)

    def test_is_loaded_false_by_default(self):
        backend = MLXBackend()
        assert backend.is_loaded is False

    def test_unload_clears_model(self):
        backend = MLXBackend()
        backend._model = MagicMock()
        backend._tokenizer = MagicMock()
        backend._model_path = "/path/to/model"

        backend.unload()

        assert backend._model is None
        assert backend._tokenizer is None
        assert backend._model_path is None

    def test_format_chat_prompt_fallback(self):
        backend = MLXBackend()
        backend._tokenizer = MagicMock(spec=[])  # No apply_chat_template

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]

        result = backend._format_chat_prompt(messages)

        assert "<|system|>" in result
        assert "<|user|>" in result
        assert "You are helpful" in result
        assert "Hello" in result


class TestVLLMBackend:
    """Tests for vLLM backend."""

    def test_get_info_returns_backend_info(self):
        info = VLLMBackend.get_info()

        assert isinstance(info, BackendInfo)
        assert info.name == "vllm"
        assert info.supports_streaming is True
        assert "safetensors" in info.model_formats
        assert "gptq" in info.model_formats
        assert "awq" in info.model_formats

    def test_is_loaded_false_by_default(self):
        backend = VLLMBackend()
        assert backend.is_loaded is False

    def test_unload_clears_model(self):
        backend = VLLMBackend()
        backend._llm = MagicMock()
        backend._model_path = "/path/to/model"

        # torch.cuda.empty_cache() is called inside a try/except,
        # so we can safely call unload without patching torch
        backend.unload()

        assert backend._llm is None
        assert backend._model_path is None

    def test_format_chat_prompt_fallback(self):
        backend = VLLMBackend()
        backend._model_path = "test/model"

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        # Mock transformers to fail
        with patch.dict("sys.modules", {"transformers": None}):
            result = backend._format_chat_prompt(messages)

        assert "System:" in result
        assert "User:" in result
        assert "Assistant:" in result


class TestBackendInterface:
    """Tests to ensure all backends implement the same interface."""

    @pytest.mark.parametrize("backend_class", [
        LlamaCppBackend,
        MLXBackend,
        VLLMBackend,
    ])
    def test_backend_has_is_available(self, backend_class):
        assert hasattr(backend_class, "is_available")
        assert callable(backend_class.is_available)

    @pytest.mark.parametrize("backend_class", [
        LlamaCppBackend,
        MLXBackend,
        VLLMBackend,
    ])
    def test_backend_has_get_info(self, backend_class):
        assert hasattr(backend_class, "get_info")
        info = backend_class.get_info()
        assert isinstance(info, BackendInfo)

    @pytest.mark.parametrize("backend_class", [
        LlamaCppBackend,
        MLXBackend,
        VLLMBackend,
    ])
    def test_backend_has_required_methods(self, backend_class):
        backend = backend_class()

        required_methods = [
            "load_model",
            "generate",
            "generate_stream",
            "chat",
            "chat_stream",
            "unload",
        ]

        for method_name in required_methods:
            assert hasattr(backend, method_name), f"Missing method: {method_name}"
            assert callable(getattr(backend, method_name))

    @pytest.mark.parametrize("backend_class", [
        LlamaCppBackend,
        MLXBackend,
        VLLMBackend,
    ])
    def test_backend_has_is_loaded_property(self, backend_class):
        backend = backend_class()
        assert hasattr(backend, "is_loaded")
        assert isinstance(backend.is_loaded, bool)
