"""Tests for Session API."""

from unittest.mock import patch, MagicMock

import pytest

from anykernel.session import Session
from anykernel.backend.base import BackendInfo, GenerationParams
from anykernel.exceptions import SessionNotInitializedError


class MockBackend:
    """Mock backend for testing."""

    def __init__(self):
        self._loaded = False

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def get_info(cls):
        return BackendInfo(
            name="mock",
            version="1.0.0",
            supports_streaming=True,
            supports_chat=True,
            model_formats=["gguf"]
        )

    def load_model(self, model_path, **kwargs):
        self._loaded = True

    def generate(self, prompt, params=None):
        return "Generated response"

    def generate_stream(self, prompt, params=None):
        yield "Generated"
        yield " response"

    def chat(self, messages, params=None):
        return "Chat response"

    def chat_stream(self, messages, params=None):
        yield "Chat"
        yield " response"

    def unload(self):
        self._loaded = False

    @property
    def is_loaded(self):
        return self._loaded


class TestSessionInit:
    """Tests for Session initialization."""

    def test_session_init_stores_params(self):
        session = Session(
            model_id="test/model",
            model_file="test.gguf",
            backend="llama_cpp",
            log_level="debug"
        )

        assert session.model_id == "test/model"
        assert session.model_file == "test.gguf"
        assert session.backend_name == "llama_cpp"

    def test_session_not_initialized_without_context(self):
        session = Session("test/model")

        assert session._initialized is False
        assert session._backend is None


class TestSessionContextManager:
    """Tests for Session context manager."""

    @patch("anykernel.session.AnyKernelClient")
    def test_context_manager_enters_and_exits(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            assert session._initialized is True
            mock_client.load_model.assert_called_once()

        mock_client.unload.assert_called_once()

    @patch("anykernel.session.AnyKernelClient")
    def test_context_manager_sets_initialized_false_on_exit(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        session = Session("test/model")
        with session:
            pass

        assert session._initialized is False


class TestSessionMethods:
    """Tests for Session methods."""

    def test_generate_raises_when_not_initialized(self):
        session = Session("test/model")

        with pytest.raises(SessionNotInitializedError):
            session.generate("Hello")

    def test_chat_raises_when_not_initialized(self):
        session = Session("test/model")

        with pytest.raises(SessionNotInitializedError):
            session.chat("Hello")

    @patch("anykernel.session.AnyKernelClient")
    def test_generate_calls_backend(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_backend._loaded = True
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            result = session.generate("Hello")
            assert result == "Generated response"

    @patch("anykernel.session.AnyKernelClient")
    def test_chat_stores_history(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_backend._loaded = True
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            session.chat("Hello")

            # Should have user message and assistant response
            assert len(session.history) == 2
            assert session.history[0]["role"] == "user"
            assert session.history[0]["content"] == "Hello"
            assert session.history[1]["role"] == "assistant"

    @patch("anykernel.session.AnyKernelClient")
    def test_chat_with_system_prompt(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_backend._loaded = True
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            session.chat("Hello", system_prompt="You are helpful")

            # Should have system, user, and assistant messages
            assert len(session.history) == 3
            assert session.history[0]["role"] == "system"
            assert session.history[0]["content"] == "You are helpful"

    @patch("anykernel.session.AnyKernelClient")
    def test_clear_history(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_backend._loaded = True
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            session.chat("Hello")
            assert len(session.history) > 0

            session.clear_history()
            assert len(session.history) == 0


class TestSessionProperties:
    """Tests for Session properties."""

    @patch("anykernel.session.AnyKernelClient")
    def test_hardware_info_returns_dict(self, MockClient):
        mock_client = MagicMock()
        mock_client.hardware = MagicMock(
            os_name="Linux",
            arch="x86_64",
            accelerator=MagicMock(value="cpu"),
            accelerator_name="Intel",
            cpu_cores=8,
            is_apple_silicon=False
        )
        mock_backend = MockBackend()
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            info = session.hardware_info
            assert isinstance(info, dict)
            assert "os" in info
            assert "accelerator" in info

    @patch("anykernel.session.AnyKernelClient")
    def test_backend_info_when_loaded(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_backend._loaded = True
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        with Session("test/model") as session:
            info = session.backend_info
            assert isinstance(info, dict)
            assert info["name"] == "mock"
            assert info["loaded"] is True

    def test_backend_info_when_not_loaded(self):
        session = Session("test/model")
        info = session.backend_info

        assert info["name"] is None
        assert info["loaded"] is False

    def test_history_returns_copy(self):
        session = Session("test/model")
        history = session.history

        # Should return a copy, not the original
        history.append({"role": "user", "content": "test"})
        assert len(session.history) == 0


class TestSessionManualLoadUnload:
    """Tests for manual load/unload methods."""

    @patch("anykernel.session.AnyKernelClient")
    def test_manual_load(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        session = Session("test/model")
        result = session.load()

        assert result is session  # Returns self for chaining
        assert session._initialized is True

    @patch("anykernel.session.AnyKernelClient")
    def test_manual_unload(self, MockClient):
        mock_client = MagicMock()
        mock_backend = MockBackend()
        mock_client.load_model.return_value = mock_backend
        MockClient.return_value = mock_client

        session = Session("test/model")
        session.load()
        session.unload()

        assert session._initialized is False
        mock_client.unload.assert_called_once()
