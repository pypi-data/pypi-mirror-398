"""Tests for hardware detection module."""

import platform
from unittest.mock import patch, MagicMock

import pytest

from anykernel.hardware import (
    HardwareDetector,
    HardwareProfile,
    AcceleratorType,
    detect_hardware,
)


class TestAcceleratorType:
    """Tests for AcceleratorType enum."""

    def test_cpu_value(self):
        assert AcceleratorType.CPU.value == "cpu"

    def test_cuda_value(self):
        assert AcceleratorType.CUDA.value == "cuda"

    def test_metal_value(self):
        assert AcceleratorType.METAL.value == "metal"


class TestHardwareProfile:
    """Tests for HardwareProfile dataclass."""

    def test_create_profile(self):
        profile = HardwareProfile(
            os_name="Linux",
            arch="x86_64",
            cpu_cores=8,
            cpu_features=["avx2"],
            accelerator=AcceleratorType.CPU,
            accelerator_name="Intel Core",
            vram_mb=None,
            is_apple_silicon=False
        )
        assert profile.os_name == "Linux"
        assert profile.cpu_cores == 8
        assert profile.accelerator == AcceleratorType.CPU
        assert not profile.is_apple_silicon


class TestHardwareDetector:
    """Tests for HardwareDetector class."""

    def test_detector_creates_profile(self):
        """Verify detector returns a HardwareProfile."""
        detector = HardwareDetector()
        profile = detector.detect()

        assert isinstance(profile, HardwareProfile)
        assert profile.os_name in ("Windows", "Darwin", "Linux")
        assert profile.cpu_cores >= 1
        assert isinstance(profile.accelerator, AcceleratorType)

    @patch("anykernel.hardware.platform")
    def test_detects_apple_silicon(self, mock_platform):
        """Test Apple Silicon detection."""
        mock_platform.system.return_value = "Darwin"
        mock_platform.machine.return_value = "arm64"

        detector = HardwareDetector()
        is_apple = detector._is_apple_silicon("Darwin", "arm64")

        assert is_apple is True

    @patch("anykernel.hardware.platform")
    def test_not_apple_silicon_on_linux(self, mock_platform):
        """Test non-Apple Silicon on Linux."""
        mock_platform.system.return_value = "Linux"
        mock_platform.machine.return_value = "x86_64"

        detector = HardwareDetector()
        is_apple = detector._is_apple_silicon("Linux", "x86_64")

        assert is_apple is False

    @patch("anykernel.hardware.subprocess.run")
    def test_nvidia_gpu_detection_success(self, mock_run):
        """Test successful NVIDIA GPU detection."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NVIDIA GeForce RTX 3080, 10240\n"
        )

        detector = HardwareDetector()
        result = detector._detect_nvidia_gpu()

        assert result is not None
        assert result["name"] == "NVIDIA GeForce RTX 3080"
        assert result["vram_mb"] == 10240

    @patch("anykernel.hardware.subprocess.run")
    def test_nvidia_gpu_detection_not_found(self, mock_run):
        """Test no NVIDIA GPU found."""
        mock_run.side_effect = FileNotFoundError()

        detector = HardwareDetector()
        result = detector._detect_nvidia_gpu()

        assert result is None

    def test_detect_cpu_features_returns_list(self):
        """Test CPU feature detection returns a list."""
        detector = HardwareDetector()
        features = detector._detect_cpu_features()

        assert isinstance(features, list)


class TestDetectHardwareFunction:
    """Tests for the convenience detect_hardware function."""

    def test_detect_hardware_returns_profile(self):
        """Test convenience function returns HardwareProfile."""
        profile = detect_hardware()

        assert isinstance(profile, HardwareProfile)
        assert profile.os_name == platform.system()
