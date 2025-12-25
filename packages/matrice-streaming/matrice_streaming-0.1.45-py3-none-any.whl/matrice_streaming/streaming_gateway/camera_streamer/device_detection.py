"""Platform detection and capability discovery for GStreamer optimization.

This module provides hardware platform detection (Jetson, Desktop NVIDIA GPU, Intel/AMD GPU, CPU-only)
and GStreamer element capability checking to enable platform-specific pipeline optimization.
"""
import logging
import os
import platform
import subprocess
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

# GStreamer imports
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    GST_AVAILABLE = True
except (ImportError, ValueError):
    GST_AVAILABLE = False


class PlatformType(Enum):
    """Supported hardware platform types."""
    JETSON = "jetson"
    DESKTOP_NVIDIA_GPU = "desktop-nvidia-gpu"
    INTEL_GPU = "intel-gpu"
    AMD_GPU = "amd-gpu"
    CPU_ONLY = "cpu-only"


@dataclass
class PlatformInfo:
    """Detected platform information and capabilities."""

    platform_type: PlatformType
    model: str  # e.g., "Jetson Xavier NX", "RTX 4090", "Intel UHD Graphics"
    architecture: str  # x86_64, aarch64, etc.

    # GStreamer element availability
    available_encoders: Set[str] = field(default_factory=set)
    available_decoders: Set[str] = field(default_factory=set)
    available_converters: Set[str] = field(default_factory=set)

    # Hardware capabilities
    supports_nvmm: bool = False  # NVIDIA Memory Model (Jetson)
    supports_cuda_memory: bool = False  # CUDA memory (Desktop NVIDIA)
    supports_vaapi: bool = False  # Video Acceleration API (Intel/AMD)
    gpu_count: int = 0

    # Recommended settings
    recommended_encoder: str = "jpeg"
    recommended_decoder: str = "avdec_h264"
    recommended_converter: str = "videoconvert"
    max_workers: Optional[int] = None  # Platform-appropriate worker count

    def __str__(self) -> str:
        return (
            f"Platform: {self.platform_type.value}, Model: {self.model}, "
            f"Arch: {self.architecture}, GPUs: {self.gpu_count}"
        )


class PlatformDetector:
    """Singleton platform detector with caching.

    Detects hardware platform and GStreamer capabilities, caching results
    for efficient reuse across multiple pipeline instances.
    """

    _instance: Optional['PlatformDetector'] = None
    _lock = threading.RLock()
    _platform_info: Optional[PlatformInfo] = None

    def __init__(self):
        """Private constructor - use get_instance() instead."""
        self.logger = logging.getLogger(__name__)

        # Initialize GStreamer if not already done
        if GST_AVAILABLE and not Gst.is_initialized():
            Gst.init(None)

    @classmethod
    def get_instance(cls) -> 'PlatformDetector':
        """Get singleton instance of PlatformDetector."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def detect(self, force_redetect: bool = False) -> PlatformInfo:
        """Detect platform and cache results.

        Args:
            force_redetect: Force re-detection even if cached result exists

        Returns:
            PlatformInfo with detected capabilities
        """
        with self._lock:
            if self._platform_info and not force_redetect:
                return self._platform_info

            self.logger.info("Detecting hardware platform...")

            # Detect platform type
            platform_type, model = self._detect_platform_type()
            architecture = platform.machine()

            # Create PlatformInfo
            platform_info = PlatformInfo(
                platform_type=platform_type,
                model=model,
                architecture=architecture,
            )

            # Detect GPU count
            platform_info.gpu_count = self._detect_gpu_count(platform_type)

            # Detect GStreamer capabilities
            self._detect_gstreamer_capabilities(platform_info)

            # Set recommended settings
            self._set_recommended_settings(platform_info)

            # Cache and return
            self._platform_info = platform_info

            self.logger.info(f"Platform detected: {platform_info}")
            self.logger.info(
                f"Available encoders: {', '.join(sorted(platform_info.available_encoders))}"
            )

            return platform_info

    def override_platform(self, platform_type: PlatformType, model: str = "Manual Override"):
        """Manually override platform detection (for testing).

        Args:
            platform_type: Platform type to force
            model: Optional model description
        """
        with self._lock:
            self.logger.warning(f"Manually overriding platform to: {platform_type.value}")

            platform_info = PlatformInfo(
                platform_type=platform_type,
                model=model,
                architecture=platform.machine(),
            )

            # Still detect GStreamer capabilities for overridden platform
            self._detect_gstreamer_capabilities(platform_info)
            self._set_recommended_settings(platform_info)

            self._platform_info = platform_info

    def clear_cache(self):
        """Clear cached platform detection results."""
        with self._lock:
            self._platform_info = None
            self.logger.info("Cleared platform detection cache")

    def _detect_platform_type(self) -> tuple:
        """Detect platform type and model.

        Returns:
            Tuple of (PlatformType, model_string)
        """
        # Check for Jetson (ARM + NVIDIA)
        if self._is_jetson():
            model = self._get_jetson_model()
            return (PlatformType.JETSON, model)

        # Check for Desktop NVIDIA GPU
        if self._has_nvidia_gpu():
            model = self._get_nvidia_gpu_model()
            return (PlatformType.DESKTOP_NVIDIA_GPU, model)

        # Check for Intel GPU
        if self._has_intel_gpu():
            model = self._get_intel_gpu_model()
            return (PlatformType.INTEL_GPU, model)

        # Check for AMD GPU
        if self._has_amd_gpu():
            model = self._get_amd_gpu_model()
            return (PlatformType.AMD_GPU, model)

        # Fallback to CPU-only
        return (PlatformType.CPU_ONLY, f"{platform.processor() or 'Unknown CPU'}")

    def _is_jetson(self) -> bool:
        """Check if running on NVIDIA Jetson device."""
        try:
            # Check device tree model (definitive Jetson check)
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().lower()
                    if 'jetson' in model:
                        return True

            # Secondary check: ARM architecture + nvidia-smi
            if platform.machine() in ('aarch64', 'armv8', 'arm64'):
                if self._has_nvidia_gpu():
                    return True

        except Exception as e:
            self.logger.debug(f"Jetson detection error: {e}")

        return False

    def _get_jetson_model(self) -> str:
        """Get Jetson model name."""
        try:
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip().replace('\x00', '')
                    return model
        except Exception:
            pass

        return "Jetson (Unknown Model)"

    def _has_nvidia_gpu(self) -> bool:
        """Check if NVIDIA GPU is available."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_nvidia_gpu_model(self) -> str:
        """Get NVIDIA GPU model name."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass

        return "NVIDIA GPU (Unknown Model)"

    def _has_intel_gpu(self) -> bool:
        """Check if Intel GPU with VAAPI is available."""
        try:
            result = subprocess.run(
                ['vainfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and 'Intel' in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_intel_gpu_model(self) -> str:
        """Get Intel GPU model name."""
        try:
            result = subprocess.run(
                ['vainfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse vainfo output for GPU info
                for line in result.stdout.split('\n'):
                    if 'Intel' in line and ('Graphics' in line or 'HD' in line or 'Iris' in line):
                        return line.strip()
        except Exception:
            pass

        return "Intel GPU (Unknown Model)"

    def _has_amd_gpu(self) -> bool:
        """Check if AMD GPU with VAAPI is available."""
        try:
            result = subprocess.run(
                ['vainfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0 and 'AMD' in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _get_amd_gpu_model(self) -> str:
        """Get AMD GPU model name."""
        try:
            result = subprocess.run(
                ['vainfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'AMD' in line or 'Radeon' in line:
                        return line.strip()
        except Exception:
            pass

        return "AMD GPU (Unknown Model)"

    def _detect_gpu_count(self, platform_type: PlatformType) -> int:
        """Detect number of available GPUs."""
        if platform_type == PlatformType.CPU_ONLY:
            return 0

        try:
            if platform_type in (PlatformType.JETSON, PlatformType.DESKTOP_NVIDIA_GPU):
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return len([line for line in result.stdout.strip().split('\n') if line])
        except Exception:
            pass

        return 1  # Assume at least 1 GPU if detection succeeded

    def _detect_gstreamer_capabilities(self, platform_info: PlatformInfo):
        """Detect available GStreamer elements."""
        if not GST_AVAILABLE:
            self.logger.warning("GStreamer not available, skipping capability detection")
            return

        # Encoders to check
        encoders_to_check = {
            # JPEG encoders
            'nvjpegenc': PlatformType.JETSON,  # Jetson hardware JPEG
            'vaapijpegenc': (PlatformType.INTEL_GPU, PlatformType.AMD_GPU),  # VAAPI JPEG
            'jpegenc': None,  # CPU JPEG (always available if gst-plugins-good installed)

            # H.264/H.265 encoders
            'nvh264enc': (PlatformType.DESKTOP_NVIDIA_GPU, PlatformType.JETSON),  # NVENC H.264
            'nvh265enc': (PlatformType.DESKTOP_NVIDIA_GPU, PlatformType.JETSON),  # NVENC H.265
            'nvv4l2h264enc': PlatformType.JETSON,  # Jetson V4L2 H.264
            'nvv4l2h265enc': PlatformType.JETSON,  # Jetson V4L2 H.265
            'vaapih264enc': (PlatformType.INTEL_GPU, PlatformType.AMD_GPU),  # VAAPI H.264
            'vaapih265enc': (PlatformType.INTEL_GPU, PlatformType.AMD_GPU),  # VAAPI H.265
            'x264enc': None,  # CPU H.264
            'openh264enc': None,  # OpenH264
        }

        # Decoders to check
        decoders_to_check = {
            'nvv4l2decoder': PlatformType.JETSON,  # Jetson hardware decoder
            'nvdec': PlatformType.DESKTOP_NVIDIA_GPU,  # Desktop NVIDIA decoder
            'vaapih264dec': (PlatformType.INTEL_GPU, PlatformType.AMD_GPU),  # VAAPI decoder
            'avdec_h264': None,  # CPU decoder
        }

        # Converters to check
        converters_to_check = {
            'nvvidconv': PlatformType.JETSON,  # Jetson GPU converter
            'cudaconvert': (PlatformType.DESKTOP_NVIDIA_GPU, PlatformType.JETSON),  # CUDA converter
            'videoconvert': None,  # CPU converter
        }

        # Check encoders
        for encoder, expected_platform in encoders_to_check.items():
            if self._check_gstreamer_element(encoder):
                platform_info.available_encoders.add(encoder)

        # Check decoders
        for decoder, expected_platform in decoders_to_check.items():
            if self._check_gstreamer_element(decoder):
                platform_info.available_decoders.add(decoder)

        # Check converters
        for converter, expected_platform in converters_to_check.items():
            if self._check_gstreamer_element(converter):
                platform_info.available_converters.add(converter)

        # Set capability flags
        platform_info.supports_nvmm = (
            platform_info.platform_type == PlatformType.JETSON and
            'nvvidconv' in platform_info.available_converters
        )

        platform_info.supports_cuda_memory = (
            platform_info.platform_type == PlatformType.DESKTOP_NVIDIA_GPU and
            'nvh264enc' in platform_info.available_encoders
        )

        platform_info.supports_vaapi = (
            platform_info.platform_type in (PlatformType.INTEL_GPU, PlatformType.AMD_GPU) and
            len(platform_info.available_encoders & {'vaapih264enc', 'vaapijpegenc'}) > 0
        )

    def _check_gstreamer_element(self, element_name: str) -> bool:
        """Check if a GStreamer element is available.

        Args:
            element_name: Name of GStreamer element to check

        Returns:
            True if element is available, False otherwise
        """
        if not GST_AVAILABLE:
            return False

        try:
            # Try to create element
            element = Gst.ElementFactory.make(element_name, None)
            if element is not None:
                return True

            # Alternative: Check factory
            factory = Gst.ElementFactory.find(element_name)
            return factory is not None

        except Exception as e:
            self.logger.debug(f"Element {element_name} not available: {e}")
            return False

    def _set_recommended_settings(self, platform_info: PlatformInfo):
        """Set recommended encoder/decoder based on platform."""

        # Recommended JPEG encoder
        if platform_info.platform_type == PlatformType.JETSON:
            if 'nvjpegenc' in platform_info.available_encoders:
                platform_info.recommended_encoder = "nvjpegenc"
            else:
                platform_info.recommended_encoder = "jpeg"  # Fallback to CPU

        elif platform_info.platform_type in (PlatformType.INTEL_GPU, PlatformType.AMD_GPU):
            if 'vaapijpegenc' in platform_info.available_encoders:
                platform_info.recommended_encoder = "vaapijpegenc"
            else:
                platform_info.recommended_encoder = "jpeg"

        else:
            platform_info.recommended_encoder = "jpeg"  # CPU

        # Recommended decoder
        if platform_info.platform_type == PlatformType.JETSON:
            if 'nvv4l2decoder' in platform_info.available_decoders:
                platform_info.recommended_decoder = "nvv4l2decoder"
            else:
                platform_info.recommended_decoder = "avdec_h264"

        elif platform_info.platform_type == PlatformType.DESKTOP_NVIDIA_GPU:
            if 'nvdec' in platform_info.available_decoders:
                platform_info.recommended_decoder = "nvdec"
            else:
                platform_info.recommended_decoder = "avdec_h264"

        elif platform_info.platform_type in (PlatformType.INTEL_GPU, PlatformType.AMD_GPU):
            if 'vaapih264dec' in platform_info.available_decoders:
                platform_info.recommended_decoder = "vaapih264dec"
            else:
                platform_info.recommended_decoder = "avdec_h264"

        else:
            platform_info.recommended_decoder = "avdec_h264"

        # Recommended converter
        if 'nvvidconv' in platform_info.available_converters:
            platform_info.recommended_converter = "nvvidconv"
        elif 'cudaconvert' in platform_info.available_converters:
            platform_info.recommended_converter = "cudaconvert"
        else:
            platform_info.recommended_converter = "videoconvert"

        # Recommended max workers (platform-appropriate)
        if platform_info.platform_type == PlatformType.JETSON:
            # Jetson has fewer cores, limit workers
            platform_info.max_workers = 8
        elif platform_info.platform_type == PlatformType.CPU_ONLY:
            # CPU-only needs more workers for parallelism
            platform_info.max_workers = min(os.cpu_count() or 4, 16)
        else:
            # GPU-accelerated can handle more cameras per worker
            platform_info.max_workers = None  # No hard limit


def get_platform_info(force_redetect: bool = False) -> PlatformInfo:
    """Convenience function to get platform information.

    Args:
        force_redetect: Force re-detection even if cached

    Returns:
        PlatformInfo with detected capabilities
    """
    detector = PlatformDetector.get_instance()
    return detector.detect(force_redetect=force_redetect)
