"""Tests for model caching utilities."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from anykernel.utils.cache import ModelCache
from anykernel.exceptions import ModelNotFoundError, ModelDownloadError


class TestModelCacheInit:
    """Tests for ModelCache initialization."""

    def test_default_cache_dir(self):
        cache = ModelCache()
        expected = Path.home() / ".anykernel" / "models"
        assert cache.cache_dir == expected

    def test_custom_cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_cache"
            cache = ModelCache(cache_dir=custom_dir)
            assert cache.cache_dir == custom_dir
            assert custom_dir.exists()


class TestKnownModels:
    """Tests for known model mappings."""

    def test_known_models_contains_tinyllama(self):
        assert "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF" in ModelCache.KNOWN_MODELS

    def test_known_models_have_gguf_filenames(self):
        for model_id, filename in ModelCache.KNOWN_MODELS.items():
            assert filename.endswith(".gguf"), f"{model_id} should have .gguf filename"


class TestGetModelPath:
    """Tests for get_model_path method."""

    def test_local_file_returns_directly(self):
        with tempfile.NamedTemporaryFile(suffix=".gguf", delete=False) as f:
            local_path = f.name

        try:
            cache = ModelCache()
            result = cache.get_model_path(local_path)
            assert result == local_path
        finally:
            os.unlink(local_path)

    def test_nonexistent_local_gguf_raises_error(self):
        cache = ModelCache()

        with pytest.raises(ModelNotFoundError):
            cache.get_model_path("/nonexistent/path/model.gguf")

    def test_unknown_model_without_filename_raises_error(self):
        cache = ModelCache()

        with pytest.raises(ValueError) as exc_info:
            cache.get_model_path("unknown/model")

        assert "Unknown model" in str(exc_info.value)

    @patch("huggingface_hub.hf_hub_download")
    def test_known_model_downloads_automatically(self, mock_download):
        mock_download.return_value = "/cached/path/model.gguf"

        cache = ModelCache()
        result = cache.get_model_path("TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF")

        assert result == "/cached/path/model.gguf"
        mock_download.assert_called_once()

    @patch("huggingface_hub.hf_hub_download")
    def test_custom_filename_downloads(self, mock_download):
        mock_download.return_value = "/cached/path/custom.gguf"

        cache = ModelCache()
        result = cache.get_model_path(
            "some/model",
            filename="custom.gguf"
        )

        assert result == "/cached/path/custom.gguf"
        call_args = mock_download.call_args
        assert call_args.kwargs["filename"] == "custom.gguf"


class TestCacheManagement:
    """Tests for cache management methods."""

    def test_list_cached_models_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(cache_dir=Path(tmpdir))
            models = cache.list_cached_models()
            assert models == []

    def test_list_cached_models_finds_gguf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = ModelCache(cache_dir=cache_dir)

            # Create a fake gguf file
            fake_model = cache_dir / "model.gguf"
            fake_model.write_text("fake model data")

            models = cache.list_cached_models()
            assert len(models) == 1
            assert models[0].endswith("model.gguf")

    def test_get_cache_size_mb_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(cache_dir=Path(tmpdir))
            size = cache.get_cache_size_mb()
            assert size == 0.0

    def test_get_cache_size_mb_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = ModelCache(cache_dir=cache_dir)

            # Create a file with known size (1MB = 1024*1024 bytes)
            fake_file = cache_dir / "file.bin"
            fake_file.write_bytes(b"x" * (1024 * 1024))

            size = cache.get_cache_size_mb()
            assert abs(size - 1.0) < 0.01  # Approximately 1MB

    def test_clear_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = ModelCache(cache_dir=cache_dir)

            # Create some files
            (cache_dir / "model.gguf").write_text("data")
            (cache_dir / "subdir").mkdir()
            (cache_dir / "subdir" / "other.gguf").write_text("data")

            cache.clear_cache()

            # Directory should exist but be empty
            assert cache_dir.exists()
            assert len(list(cache_dir.iterdir())) == 0

    def test_remove_model_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = ModelCache(cache_dir=cache_dir)

            model_path = cache_dir / "model.gguf"
            model_path.write_text("data")

            result = cache.remove_model(str(model_path))

            assert result is True
            assert not model_path.exists()

    def test_remove_model_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ModelCache(cache_dir=Path(tmpdir))

            result = cache.remove_model("/nonexistent/model.gguf")

            assert result is False
