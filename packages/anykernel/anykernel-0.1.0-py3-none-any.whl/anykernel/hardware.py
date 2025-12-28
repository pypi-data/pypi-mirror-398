"""Hardware detection for AnyKernel."""

import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .utils.logger import get_logger


class AcceleratorType(Enum):
    """Types of hardware accelerators."""
    CPU = "cpu"
    CUDA = "cuda"       # NVIDIA GPU
    METAL = "metal"     # Apple Silicon


@dataclass
class HardwareProfile:
    """Detected hardware profile."""
    os_name: str                        # "Windows", "Darwin", "Linux"
    arch: str                           # "x86_64", "arm64", "AMD64"
    cpu_cores: int                      # Number of CPU cores
    cpu_features: List[str]             # CPU features like "avx2", "avx512"
    accelerator: AcceleratorType        # Best available accelerator
    accelerator_name: Optional[str]     # Device name (e.g., "NVIDIA RTX 3080")
    vram_mb: Optional[int]              # GPU VRAM in MB (if applicable)
    is_apple_silicon: bool              # True if Apple Silicon


class HardwareDetector:
    """Detects hardware capabilities for optimal backend selection."""

    def __init__(self):
        self.logger = get_logger()

    def detect(self) -> HardwareProfile:
        """Detect and return the hardware profile."""
        self.logger.info("Detecting hardware...")

        os_name = platform.system()
        arch = platform.machine()
        cpu_cores = os.cpu_count() or 1
        cpu_features = self._detect_cpu_features()

        # Check for Apple Silicon first
        if self._is_apple_silicon(os_name, arch):
            profile = HardwareProfile(
                os_name=os_name,
                arch=arch,
                cpu_cores=cpu_cores,
                cpu_features=cpu_features,
                accelerator=AcceleratorType.METAL,
                accelerator_name=self._get_apple_chip_name(),
                vram_mb=None,  # Unified memory
                is_apple_silicon=True
            )
            self.logger.info(f"Found: Apple Silicon ({profile.accelerator_name})")
            return profile

        # Check for NVIDIA GPU
        nvidia_info = self._detect_nvidia_gpu()
        if nvidia_info:
            profile = HardwareProfile(
                os_name=os_name,
                arch=arch,
                cpu_cores=cpu_cores,
                cpu_features=cpu_features,
                accelerator=AcceleratorType.CUDA,
                accelerator_name=nvidia_info["name"],
                vram_mb=nvidia_info.get("vram_mb"),
                is_apple_silicon=False
            )
            self.logger.info(f"Found: NVIDIA GPU ({profile.accelerator_name})")
            return profile

        # Fallback to CPU
        cpu_name = self._get_cpu_name()
        profile = HardwareProfile(
            os_name=os_name,
            arch=arch,
            cpu_cores=cpu_cores,
            cpu_features=cpu_features,
            accelerator=AcceleratorType.CPU,
            accelerator_name=cpu_name,
            vram_mb=None,
            is_apple_silicon=False
        )
        self.logger.info(f"Found: CPU ({cpu_cores} cores)")
        return profile

    def _is_apple_silicon(self, os_name: str, arch: str) -> bool:
        """Check if running on Apple Silicon."""
        return os_name == "Darwin" and arch == "arm64"

    def _get_apple_chip_name(self) -> str:
        """Get Apple chip name via sysctl."""
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return "Apple Silicon"

    def _detect_nvidia_gpu(self) -> Optional[dict]:
        """Detect NVIDIA GPU using nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                line = result.stdout.strip().split('\n')[0]
                parts = line.split(', ')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    try:
                        vram = int(parts[1].strip())
                    except ValueError:
                        vram = None
                    return {"name": name, "vram_mb": vram}
                elif len(parts) == 1:
                    return {"name": parts[0].strip(), "vram_mb": None}
        except FileNotFoundError:
            # nvidia-smi not found
            pass
        except Exception:
            pass
        return None

    def _get_cpu_name(self) -> str:
        """Get CPU name."""
        try:
            if platform.system() == "Windows":
                return platform.processor() or "Unknown CPU"
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            elif platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("model name"):
                            return line.split(":")[1].strip()
        except Exception:
            pass
        return platform.processor() or "Unknown CPU"

    def _detect_cpu_features(self) -> List[str]:
        """Detect CPU features like AVX2, AVX512."""
        features = []

        try:
            if platform.system() == "Windows":
                # On Windows, we can't easily detect CPU features without additional deps
                # Return common features based on architecture
                if platform.machine() in ("AMD64", "x86_64"):
                    features = ["sse", "sse2", "avx"]  # Assume basic features
            elif platform.system() == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.features"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    cpu_features = result.stdout.strip().lower().split()
                    # Map to standard feature names
                    if "avx2" in cpu_features or "avx2.0" in cpu_features:
                        features.append("avx2")
                    if "avx512" in " ".join(cpu_features):
                        features.append("avx512")
                    if "avx1.0" in cpu_features or "avx" in cpu_features:
                        features.append("avx")
            elif platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if line.startswith("flags"):
                            flags = line.split(":")[1].strip().split()
                            if "avx2" in flags:
                                features.append("avx2")
                            if "avx512f" in flags:
                                features.append("avx512")
                            if "avx" in flags:
                                features.append("avx")
                            break
        except Exception:
            pass

        return features


def detect_hardware() -> HardwareProfile:
    """Convenience function to detect hardware.

    Returns:
        HardwareProfile with detected capabilities
    """
    detector = HardwareDetector()
    return detector.detect()
