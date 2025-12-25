"""Platform-specific GStreamer pipeline builders.

This module implements the Strategy pattern for constructing optimized GStreamer pipelines
based on detected hardware platform (Jetson, Desktop NVIDIA GPU, Intel/AMD GPU, CPU-only).

Each builder encapsulates platform-specific optimizations:
- Jetson: nvjpegenc, nvvidconv, NVMM memory, nvv4l2decoder
- Desktop NVIDIA GPU: nvdec decode, nvh264enc encode, CPU jpegenc (no HW JPEG)
- Intel/AMD GPU: VAAPI (vaapijpegenc, vaapih264dec)
- CPU-only: Software fallback (x264enc, jpegenc, avdec_h264)
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional

from .device_detection import PlatformInfo, PlatformType
from .gstreamer_camera_streamer import GStreamerConfig


class PipelineBuilder(ABC):
    """Abstract base class for platform-specific pipeline builders.

    Implements Template Method pattern with platform-specific overrides.
    """

    def __init__(self, config: GStreamerConfig, platform_info: PlatformInfo):
        """Initialize pipeline builder.

        Args:
            config: GStreamer configuration
            platform_info: Detected platform information
        """
        self.config = config
        self.platform_info = platform_info
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def build_decode_element(self, source_type: str, source: str) -> str:
        """Build hardware-accelerated decode element for source.

        Args:
            source_type: Type of source (rtsp, file, camera)
            source: Source URI or path

        Returns:
            GStreamer decode element string
        """
        pass

    @abstractmethod
    def build_convert_element(self) -> str:
        """Build color conversion element (CPU or GPU accelerated).

        Returns:
            GStreamer converter element string
        """
        pass

    @abstractmethod
    def build_encode_element(self, encoder: str, quality: int, bitrate: int) -> Tuple[str, str]:
        """Build encoder element and output caps.

        Args:
            encoder: Encoder type (jpeg, h264, h265)
            quality: Quality setting (JPEG quality or video quality hint)
            bitrate: Bitrate for video encoders (bps)

        Returns:
            Tuple of (encoder_string, output_caps)
        """
        pass

    @abstractmethod
    def build_memory_element(self, encoder: str) -> str:
        """Build memory transfer/format element (NVMM, CUDA, standard).

        Args:
            encoder: Encoder type being used

        Returns:
            GStreamer memory/format caps string
        """
        pass

    def build_complete_pipeline(self, builder_config: Dict) -> str:
        """Build complete GStreamer pipeline (Template Method).

        Args:
            builder_config: Pipeline configuration dict with:
                - source_type: str
                - source: str
                - width: int
                - height: int
                - fps: int
                - encoder: str
                - quality: int
                - bitrate: int

        Returns:
            Complete GStreamer pipeline string
        """
        source_type = builder_config['source_type']
        source = builder_config['source']
        width = builder_config['width']
        height = builder_config['height']
        fps = builder_config['fps']
        encoder = builder_config['encoder']
        quality = builder_config['quality']
        bitrate = builder_config['bitrate']

        # Build pipeline elements
        decode = self.build_decode_element(source_type, source)
        convert = self.build_convert_element()
        memory_caps = self.build_memory_element(encoder)
        encode_elem, caps_out = self.build_encode_element(encoder, quality, bitrate)

        # Assemble pipeline
        pipeline = self._assemble_pipeline(
            decode, convert, memory_caps, encode_elem, caps_out,
            width, height, fps
        )

        if self.config.verbose_pipeline_logging:
            self.logger.info(f"Pipeline: {pipeline}")

        return pipeline

    def _assemble_pipeline(
        self,
        decode: str,
        convert: str,
        memory_caps: str,
        encode: str,
        caps_out: str,
        width: int,
        height: int,
        fps: int
    ) -> str:
        """Assemble complete pipeline from components.

        Args:
            decode: Decode element string
            convert: Convert element string
            memory_caps: Memory/format caps string
            encode: Encode element string
            caps_out: Output caps string
            width: Target width
            height: Target height
            fps: Target FPS

        Returns:
            Complete pipeline string
        """
        # Build pipeline with appropriate queue settings
        # Use smaller buffer for hardware encoders (nvh264enc, nvh265enc, nvjpegenc, nvv4l2h264enc, etc.)
        is_hw_encoder = any(hw in encode for hw in ['nvh264enc', 'nvh265enc', 'nvjpegenc', 'nvv4l2', 'vaapi'])
        buffer_size = 1 if is_hw_encoder else 2

        if memory_caps:
            # Hardware-accelerated pipeline with specific memory format
            pipeline = (
                f"{decode} ! "
                f"{convert} ! "
                f"video/x-raw,width={width},height={height} ! "
                f"{memory_caps} ! "
                f"videorate ! video/x-raw,framerate={fps}/1 ! "
                f"queue max-size-buffers={buffer_size} leaky=downstream ! "
                f"{encode} ! {caps_out} ! "
                f"queue max-size-buffers={buffer_size} leaky=downstream ! "
                f"appsink name=sink sync=false async=false "
                f"max-buffers={buffer_size} drop=true enable-last-sample=false"
            )
        else:
            # Standard pipeline
            pipeline = (
                f"{decode} ! "
                f"{convert} ! "
                f"videoscale ! "
                f"video/x-raw,width={width},height={height} ! "
                f"videorate ! video/x-raw,framerate={fps}/1 ! "
                f"queue max-size-buffers={buffer_size} leaky=downstream ! "
                f"{encode} ! {caps_out} ! "
                f"queue max-size-buffers={buffer_size} leaky=downstream ! "
                f"appsink name=sink sync=false async=false "
                f"max-buffers={buffer_size} drop=true enable-last-sample=false"
            )

        return pipeline

    def build_dual_appsink_pipeline(self, builder_config: Dict) -> str:
        """Build pipeline with dual appsinks for FrameOptimizer.

        Args:
            builder_config: Pipeline configuration dict

        Returns:
            Pipeline string with similarity-sink and output-sink
        """
        source_type = builder_config['source_type']
        source = builder_config['source']
        width = builder_config['width']
        height = builder_config['height']
        fps = builder_config['fps']
        encoder = builder_config['encoder']
        quality = builder_config['quality']
        bitrate = builder_config['bitrate']

        # Build pipeline elements
        decode = self.build_decode_element(source_type, source)
        convert = self.build_convert_element()
        memory_caps = self.build_memory_element(encoder)
        encode_elem, caps_out = self.build_encode_element(encoder, quality, bitrate)

        # Similarity detection: downscale to 160x120 for performance (16x fewer pixels)
        similarity_width = 160
        similarity_height = 120

        # Build dual-sink pipeline with tee
        pipeline = (
            f"{decode} ! "
            f"{convert} ! "
            f"video/x-raw,width={width},height={height} ! "
            f"videorate ! video/x-raw,framerate={fps}/1 ! "
            f"tee name=t "
            # Branch 1: Similarity detection (downscaled, raw frames)
            f"t. ! queue max-size-buffers=1 leaky=downstream ! "
            f"videoscale ! video/x-raw,width={similarity_width},height={similarity_height},format=RGB ! "
            f"appsink name=similarity-sink sync=false async=false max-buffers=1 drop=true enable-last-sample=false "
            # Branch 2: Full encode for output
            f"t. ! queue max-size-buffers=1 leaky=downstream ! "
        )

        # Add memory caps if needed (for hardware encoding)
        if memory_caps:
            pipeline += f"{memory_caps} ! "

        pipeline += (
            f"{encode_elem} ! {caps_out} ! "
            f"appsink name=output-sink sync=false async=false max-buffers=1 drop=true enable-last-sample=false"
        )

        if self.config.verbose_pipeline_logging:
            self.logger.info(f"Dual-appsink pipeline: {pipeline}")

        return pipeline


class JetsonPipelineBuilder(PipelineBuilder):
    """Jetson-optimized pipeline builder.

    Optimizations:
    - nvjpegenc for hardware JPEG encoding (10x faster than CPU)
    - nvvidconv for GPU-accelerated color conversion
    - NVMM zero-copy memory
    - nvv4l2decoder for hardware video decode
    - nvv4l2h264enc/h265enc for hardware video encode
    """

    def build_decode_element(self, source_type: str, source: str) -> str:
        if not self.config.use_hardware_decode:
            return self._build_cpu_decode(source_type, source)

        if source_type == "rtsp":
            # RTSP with hardware decode
            return (
                f"rtspsrc location={source} latency=50 buffer-mode=auto ! "
                f"rtph264depay ! h264parse ! "
                f"nvv4l2decoder enable-max-performance=1"
            )
        elif source_type == "file":
            # Video file with hardware decode
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov', 'm4v'):
                return (
                    f"filesrc location={source} ! qtdemux ! h264parse ! "
                    f"nvv4l2decoder"
                )
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! h264parse ! nvv4l2decoder"
            elif ext == 'avi':
                return f"filesrc location={source} ! avidemux ! h264parse ! nvv4l2decoder"
            else:
                # Unknown format, try qtdemux
                return f"filesrc location={source} ! qtdemux ! h264parse ! nvv4l2decoder"

        # Fallback
        return self._build_cpu_decode(source_type, source)

    def _build_cpu_decode(self, source_type: str, source: str) -> str:
        """Fallback CPU decode."""
        if source_type == "rtsp":
            return (
                f"rtspsrc location={source} latency=100 ! "
                f"rtph264depay ! h264parse ! avdec_h264"
            )
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov'):
                return f"filesrc location={source} ! qtdemux ! avdec_h264"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! avdec_h264"
            else:
                return f"filesrc location={source} ! qtdemux ! avdec_h264"

        return "videotestsrc pattern=smpte is-live=true"

    def build_convert_element(self) -> str:
        # Use nvvidconv (GPU-accelerated) instead of videoconvert
        if 'nvvidconv' in self.platform_info.available_converters:
            return "nvvidconv"
        return "videoconvert"

    def build_encode_element(self, encoder: str, quality: int, bitrate: int) -> Tuple[str, str]:
        if encoder == "jpeg":
            # Hardware JPEG encoding - HUGE performance improvement
            if 'nvjpegenc' in self.platform_info.available_encoders and self.config.use_hardware_jpeg:
                return (
                    f"nvjpegenc quality={quality}",
                    "image/jpeg"
                )
            # Fallback to CPU JPEG
            return (f"jpegenc quality={quality} idct-method=ifast", "image/jpeg")

        elif encoder == "h264":
            # Hardware H.264 encoding
            if 'nvv4l2h264enc' in self.platform_info.available_encoders:
                return (
                    f"nvv4l2h264enc preset-level=1 bitrate={bitrate} "
                    f"iframeinterval={self.config.gop_size} insert-sps-pps=true",
                    "video/x-h264,profile=main"
                )
            elif 'nvh264enc' in self.platform_info.available_encoders:
                return (
                    f"nvh264enc preset={self.config.preset} bitrate={bitrate//1000} "
                    f"gop-size={self.config.gop_size} zerolatency=true bframes=0",
                    "video/x-h264,profile=main"
                )
            # Fallback to x264
            return (
                f"x264enc speed-preset=ultrafast tune=zerolatency bitrate={bitrate//1000} threads=2",
                "video/x-h264,profile=baseline"
            )

        elif encoder == "h265":
            # Hardware H.265 encoding
            if 'nvv4l2h265enc' in self.platform_info.available_encoders:
                return (
                    f"nvv4l2h265enc preset-level=1 bitrate={bitrate} "
                    f"iframeinterval={self.config.gop_size}",
                    "video/x-h265,profile=main"
                )
            elif 'nvh265enc' in self.platform_info.available_encoders:
                return (
                    f"nvh265enc preset={self.config.preset} bitrate={bitrate//1000} "
                    f"gop-size={self.config.gop_size}",
                    "video/x-h265,profile=main"
                )

        # Unknown encoder
        raise ValueError(f"Unsupported encoder: {encoder}")

    def build_memory_element(self, encoder: str) -> str:
        # NVMM zero-copy memory for Jetson
        if self.config.jetson_use_nvmm and self.platform_info.supports_nvmm:
            if encoder == "jpeg" and 'nvjpegenc' in self.platform_info.available_encoders:
                return "video/x-raw(memory:NVMM),format=NV12"
            elif encoder in ("h264", "h265"):
                return "video/x-raw(memory:NVMM),format=NV12"
        return ""


class DesktopNvidiaGpuPipelineBuilder(PipelineBuilder):
    """Desktop NVIDIA GPU pipeline builder.

    Optimizations:
    - nvdec for hardware video decode
    - nvh264enc/nvh265enc for hardware video encode
    - CUDA memory for zero-copy (video codecs only)

    Limitations:
    - NO hardware JPEG encoding (GStreamer limitation on desktop GPUs)
    - Must use CPU jpegenc
    """

    def build_decode_element(self, source_type: str, source: str) -> str:
        if not self.config.use_hardware_decode:
            return self._build_cpu_decode(source_type, source)

        if 'nvdec' not in self.platform_info.available_decoders:
            return self._build_cpu_decode(source_type, source)

        if source_type == "rtsp":
            return (
                f"rtspsrc location={source} latency=100 buffer-mode=auto ! "
                f"rtph264depay ! h264parse ! "
                f"nvdec"
            )
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov', 'm4v'):
                return f"filesrc location={source} ! qtdemux ! h264parse ! nvdec"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! h264parse ! nvdec"
            elif ext == 'avi':
                return f"filesrc location={source} ! avidemux ! h264parse ! nvdec"
            else:
                return f"filesrc location={source} ! qtdemux ! h264parse ! nvdec"

        return self._build_cpu_decode(source_type, source)

    def _build_cpu_decode(self, source_type: str, source: str) -> str:
        if source_type == "rtsp":
            return f"rtspsrc location={source} latency=100 ! rtph264depay ! h264parse ! avdec_h264"
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov'):
                return f"filesrc location={source} ! qtdemux ! avdec_h264"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! avdec_h264"
            else:
                return f"filesrc location={source} ! qtdemux ! avdec_h264"
        return "videotestsrc pattern=smpte is-live=true"

    def build_convert_element(self) -> str:
        # Use standard videoconvert (GPU conversion for CUDA memory handled separately)
        return "videoconvert"

    def build_encode_element(self, encoder: str, quality: int, bitrate: int) -> Tuple[str, str]:
        if encoder == "jpeg":
            # LIMITATION: No hardware JPEG on desktop GPUs in GStreamer
            # Must use CPU jpegenc
            self.logger.debug("Using CPU JPEG encoding (no hardware support on desktop GPU)")
            return (
                f"jpegenc quality={quality} idct-method=ifast",
                "image/jpeg"
            )

        elif encoder == "h264":
            # Hardware H.264 encoding with NVENC
            if 'nvh264enc' in self.platform_info.available_encoders:
                return (
                    f"nvh264enc cuda-device-id={self.config.gpu_id} "
                    f"preset={self.config.preset} bitrate={bitrate//1000} "
                    f"gop-size={self.config.gop_size} zerolatency=true "
                    f"rc-lookahead=0 bframes=0 rc-mode=cbr-ld-hq",
                    "video/x-h264,profile=main"
                )
            # Fallback to x264
            return (
                f"x264enc speed-preset=ultrafast tune=zerolatency bitrate={bitrate//1000} threads=4",
                "video/x-h264,profile=baseline"
            )

        elif encoder == "h265":
            # Hardware H.265 encoding with NVENC
            if 'nvh265enc' in self.platform_info.available_encoders:
                return (
                    f"nvh265enc cuda-device-id={self.config.gpu_id} "
                    f"preset={self.config.preset} bitrate={bitrate//1000} "
                    f"gop-size={self.config.gop_size} zerolatency=true "
                    f"rc-lookahead=0 bframes=0",
                    "video/x-h265,profile=main"
                )

        raise ValueError(f"Unsupported encoder: {encoder}")

    def build_memory_element(self, encoder: str) -> str:
        # CUDA memory for video codecs (if enabled and using NVENC)
        if encoder in ("h264", "h265") and self.config.use_cuda_memory:
            if f"nv{encoder}enc" in self.platform_info.available_encoders:
                return f"cudaupload cuda-device-id={self.config.gpu_id} ! video/x-raw(memory:CUDAMemory),format=NV12"
        return ""


class IntelGpuPipelineBuilder(PipelineBuilder):
    """Intel GPU pipeline builder with VAAPI.

    Optimizations:
    - vaapijpegenc for hardware JPEG encoding
    - vaapih264enc/h265enc for hardware video encode
    - vaapih264dec for hardware video decode
    """

    def build_decode_element(self, source_type: str, source: str) -> str:
        if not self.config.use_hardware_decode or 'vaapih264dec' not in self.platform_info.available_decoders:
            return self._build_cpu_decode(source_type, source)

        if source_type == "rtsp":
            return (
                f"rtspsrc location={source} latency=100 ! "
                f"rtph264depay ! h264parse ! "
                f"vaapih264dec"
            )
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov', 'm4v'):
                return f"filesrc location={source} ! qtdemux ! h264parse ! vaapih264dec"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! h264parse ! vaapih264dec"
            else:
                return f"filesrc location={source} ! qtdemux ! h264parse ! vaapih264dec"

        return self._build_cpu_decode(source_type, source)

    def _build_cpu_decode(self, source_type: str, source: str) -> str:
        if source_type == "rtsp":
            return f"rtspsrc location={source} latency=100 ! rtph264depay ! h264parse ! avdec_h264"
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov'):
                return f"filesrc location={source} ! qtdemux ! avdec_h264"
            else:
                return f"filesrc location={source} ! matroskademux ! avdec_h264"
        return "videotestsrc pattern=smpte is-live=true"

    def build_convert_element(self) -> str:
        return "videoconvert"

    def build_encode_element(self, encoder: str, quality: int, bitrate: int) -> Tuple[str, str]:
        if encoder == "jpeg":
            # Hardware JPEG encoding via VAAPI
            if 'vaapijpegenc' in self.platform_info.available_encoders and self.config.use_hardware_jpeg:
                return (
                    f"vaapijpegenc quality={quality}",
                    "image/jpeg"
                )
            # Fallback to CPU
            return (f"jpegenc quality={quality} idct-method=ifast", "image/jpeg")

        elif encoder == "h264":
            # Hardware H.264 encoding via VAAPI
            if 'vaapih264enc' in self.platform_info.available_encoders:
                return (
                    f"vaapih264enc bitrate={bitrate//1000} rate-control=cbr keyframe-period={self.config.gop_size}",
                    "video/x-h264,profile=main"
                )
            # Fallback to x264
            return (
                f"x264enc speed-preset=ultrafast tune=zerolatency bitrate={bitrate//1000} threads=4",
                "video/x-h264,profile=baseline"
            )

        elif encoder == "h265":
            # Hardware H.265 encoding via VAAPI
            if 'vaapih265enc' in self.platform_info.available_encoders:
                return (
                    f"vaapih265enc bitrate={bitrate//1000} rate-control=cbr",
                    "video/x-h265,profile=main"
                )

        raise ValueError(f"Unsupported encoder: {encoder}")

    def build_memory_element(self, encoder: str) -> str:
        # VAAPI uses its own internal memory management
        return ""


class AmdGpuPipelineBuilder(IntelGpuPipelineBuilder):
    """AMD GPU pipeline builder with VAAPI.

    Inherits from IntelGpuPipelineBuilder as AMD uses same VAAPI interface.
    Can be extended in future for AMD-specific optimizations.
    """
    pass


class CpuOnlyPipelineBuilder(PipelineBuilder):
    """CPU-only fallback pipeline builder.

    Uses software encoders/decoders:
    - jpegenc for JPEG
    - x264enc for H.264
    - avdec_h264 for decode
    """

    def build_decode_element(self, source_type: str, source: str) -> str:
        if source_type == "rtsp":
            return (
                f"rtspsrc location={source} latency=100 buffer-mode=auto ! "
                f"rtph264depay ! h264parse ! "
                f"avdec_h264"
            )
        elif source_type == "file":
            ext = source.lower().split('.')[-1] if '.' in source else ''
            if ext in ('mp4', 'mov', 'm4v'):
                return f"filesrc location={source} ! qtdemux ! avdec_h264"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={source} ! matroskademux ! avdec_h264"
            elif ext == 'avi':
                return f"filesrc location={source} ! avidemux ! avdec_h264"
            else:
                return f"filesrc location={source} ! qtdemux ! avdec_h264"

        return "videotestsrc pattern=smpte is-live=true"

    def build_convert_element(self) -> str:
        return "videoconvert"

    def build_encode_element(self, encoder: str, quality: int, bitrate: int) -> Tuple[str, str]:
        if encoder == "jpeg":
            return (f"jpegenc quality={quality} idct-method=ifast", "image/jpeg")

        elif encoder == "h264":
            # Software H.264 encoding with x264
            threads = min(4, self.platform_info.gpu_count or 4)
            return (
                f"x264enc speed-preset=ultrafast tune=zerolatency "
                f"bitrate={bitrate//1000} key-int-max={self.config.gop_size} "
                f"bframes=0 threads={threads} sliced-threads=true",
                "video/x-h264,profile=baseline"
            )

        elif encoder == "h265":
            # Software H.265 encoding (if available)
            if 'x265enc' in self.platform_info.available_encoders:
                return (
                    f"x265enc speed-preset=ultrafast bitrate={bitrate//1000} "
                    f"key-int-max={self.config.gop_size}",
                    "video/x-h265,profile=main"
                )

        raise ValueError(f"Unsupported encoder: {encoder}")

    def build_memory_element(self, encoder: str) -> str:
        return ""


class PipelineFactory:
    """Factory for selecting appropriate pipeline builder based on platform."""

    @staticmethod
    def get_builder(config: GStreamerConfig, platform_info: PlatformInfo) -> PipelineBuilder:
        """Select and instantiate appropriate pipeline builder.

        Args:
            config: GStreamer configuration
            platform_info: Detected platform information

        Returns:
            Platform-specific PipelineBuilder instance
        """
        logger = logging.getLogger(__name__)

        # Manual override if specified (and override enabled)
        if config.platform != "auto" and config.enable_platform_override:
            platform_map = {
                "jetson": JetsonPipelineBuilder,
                "desktop-gpu": DesktopNvidiaGpuPipelineBuilder,
                "intel": IntelGpuPipelineBuilder,
                "amd": AmdGpuPipelineBuilder,
                "cpu": CpuOnlyPipelineBuilder,
            }

            builder_class = platform_map.get(config.platform)
            if builder_class:
                logger.info(f"Using manual platform override: {config.platform}")
                return builder_class(config, platform_info)
            else:
                logger.warning(f"Invalid platform override '{config.platform}', using auto-detect")

        # Auto-detect based on platform_info
        if platform_info.platform_type == PlatformType.JETSON:
            logger.info("Selected JetsonPipelineBuilder")
            return JetsonPipelineBuilder(config, platform_info)

        elif platform_info.platform_type == PlatformType.DESKTOP_NVIDIA_GPU:
            logger.info("Selected DesktopNvidiaGpuPipelineBuilder")
            return DesktopNvidiaGpuPipelineBuilder(config, platform_info)

        elif platform_info.platform_type == PlatformType.INTEL_GPU:
            logger.info("Selected IntelGpuPipelineBuilder")
            return IntelGpuPipelineBuilder(config, platform_info)

        elif platform_info.platform_type == PlatformType.AMD_GPU:
            logger.info("Selected AmdGpuPipelineBuilder")
            return AmdGpuPipelineBuilder(config, platform_info)

        else:
            logger.info("Selected CpuOnlyPipelineBuilder (fallback)")
            return CpuOnlyPipelineBuilder(config, platform_info)
