"""Model caching utilities for AnyKernel."""

import os
import shutil
from pathlib import Path
from typing import Optional

from .logger import get_logger


class ModelCache:
    """Handles model downloading and caching."""

    # Default cache directory
    DEFAULT_CACHE_DIR = Path.home() / ".anykernel" / "models"

    # Known model mappings: repo_id -> default GGUF filename
    # These are popular models with well-known quantizations
    KNOWN_MODELS = {
        # Llama 2 variants
        "TheBloke/Llama-2-7B-Chat-GGUF": "llama-2-7b-chat.Q4_K_M.gguf",
        "TheBloke/Llama-2-13B-Chat-GGUF": "llama-2-13b-chat.Q4_K_M.gguf",
        # Mistral
        "TheBloke/Mistral-7B-Instruct-v0.2-GGUF": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        # Phi
        "microsoft/Phi-3-mini-4k-instruct-gguf": "Phi-3-mini-4k-instruct-q4.gguf",
        # Small models for testing
        "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        # Qwen
        "Qwen/Qwen2-1.5B-Instruct-GGUF": "qwen2-1_5b-instruct-q4_k_m.gguf",
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the model cache.

        Args:
            cache_dir: Custom cache directory. Defaults to ~/.anykernel/models/
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()

    def get_model_path(
        self,
        model_id: str,
        filename: Optional[str] = None
    ) -> str:
        """Get path to model, downloading if necessary.

        Args:
            model_id: HuggingFace model ID or local file path
            filename: Specific GGUF filename (optional for known models)

        Returns:
            Path to the GGUF model file

        Raises:
            ValueError: If model_id is unknown and filename not provided
            ModelDownloadError: If download fails
        """
        # If model_id is a local path, use directly
        if os.path.exists(model_id):
            self.logger.info(f"Using local model: {model_id}")
            return model_id

        # Check if it's a path that looks like a file but doesn't exist
        if model_id.endswith(".gguf"):
            from ..exceptions import ModelNotFoundError
            raise ModelNotFoundError(f"Model file not found: {model_id}")

        # Determine filename for HuggingFace download
        if filename is None:
            filename = self.KNOWN_MODELS.get(model_id)
            if filename is None:
                raise ValueError(
                    f"Unknown model: {model_id}. "
                    f"Please specify filename parameter or use a known model.\n"
                    f"Known models: {', '.join(self.KNOWN_MODELS.keys())}"
                )

        self.logger.info(f"Resolving model: {model_id}")

        try:
            from huggingface_hub import hf_hub_download

            path = hf_hub_download(
                repo_id=model_id,
                filename=filename,
                cache_dir=str(self.cache_dir),
                resume_download=True
            )
            self.logger.info("Model ready.")
            return path

        except ImportError:
            from ..exceptions import ModelDownloadError
            raise ModelDownloadError(
                "huggingface_hub is required for downloading models. "
                "Install with: pip install huggingface-hub"
            )
        except Exception as e:
            from ..exceptions import ModelDownloadError
            raise ModelDownloadError(
                f"Failed to download model {model_id}/{filename}: {e}"
            )

    def list_cached_models(self) -> list:
        """List all cached model files.

        Returns:
            List of paths to cached GGUF files
        """
        models = []
        for f in self.cache_dir.rglob("*.gguf"):
            models.append(str(f))
        return models

    def get_cache_size_mb(self) -> float:
        """Get total size of cached models in MB.

        Returns:
            Total cache size in megabytes
        """
        total = 0
        for f in self.cache_dir.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total / (1024 * 1024)

    def clear_cache(self):
        """Clear all cached models."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Model cache cleared.")

    def remove_model(self, model_path: str) -> bool:
        """Remove a specific model from cache.

        Args:
            model_path: Path to the model file

        Returns:
            True if removed, False if not found
        """
        path = Path(model_path)
        if path.exists() and path.is_file():
            path.unlink()
            self.logger.info(f"Removed: {model_path}")
            return True
        return False
