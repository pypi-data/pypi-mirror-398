"""GStreamer-based CameraStreamer using hardware/software encoding.

This module provides a GStreamer-based alternative to the OpenCV-based CameraStreamer.
It supports:
- NVIDIA NVENC hardware encoding (if available)
- x264 software encoding
- OpenH264 encoding
- JPEG encoding
- Zero-copy CUDA memory pipelines (for NVENC)

The flow and API are identical to CameraStreamer for drop-in replacement.
"""
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Union, Any, List
from collections import deque

from matrice_common.stream.matrice_stream import MatriceStream, StreamType
from matrice_common.optimize import FrameOptimizer

from .stream_statistics import StreamStatistics
from .message_builder import StreamMessageBuilder
from .retry_manager import RetryManager
from ..streaming_gateway_utils import StreamingGatewayUtil

# GStreamer imports (optional - graceful degradation if not available)
GST_AVAILABLE = False
try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    from gi.repository import Gst, GstApp, GLib
    GST_AVAILABLE = True
except ImportError as e:
    logging.warning(f"GStreamer not available: {e}. GStreamerCameraStreamer will not work.")


@dataclass
class GStreamerConfig:
    """Configuration for GStreamer encoding.

    Default: JPEG for frame-by-frame streaming with maximum performance.
    JPEG provides:
    - No inter-frame dependencies (true frame-by-frame)
    - Consistent per-frame latency
    - Simple frame caching (hash-based works perfectly)
    - Maximum throughput for static scenes
    """
    # Basic encoder settings
    encoder: str = "jpeg"  # Default to JPEG for frame-by-frame (was "auto")
    codec: str = "h264"  # h264, h265 (only used for video encoders)
    bitrate: int = 4000000  # 4 Mbps (only used for video encoders)
    preset: str = "low-latency"  # nvenc preset (only used for nvenc)
    gpu_id: int = 0
    use_cuda_memory: bool = True
    jpeg_quality: int = 85  # JPEG quality (1-100, higher=better quality)
    gop_size: int = 30  # I-frame interval (only used for video encoders)

    # Platform-specific settings (NEW)
    platform: str = "auto"  # auto, jetson, desktop-gpu, cpu, intel, amd
    enable_platform_override: bool = True  # Allow manual platform override
    use_hardware_decode: bool = True  # Use nvv4l2decoder, nvdec, vaapi for decode
    use_hardware_jpeg: bool = True  # Use nvjpegenc (Jetson), vaapijpegenc (Intel/AMD)
    jetson_use_nvmm: bool = True  # NVMM zero-copy memory on Jetson
    frame_optimizer_mode: str = "hash-only"  # hash-only, dual-appsink, disabled
    source_optimization: bool = True  # Enable source-specific optimizations
    fallback_on_error: bool = True  # Graceful fallback to CPU if HW fails
    verbose_pipeline_logging: bool = False  # Debug pipeline construction
    

@dataclass  
class GStreamerMetrics:
    """Metrics for a GStreamer stream."""
    frames_processed: int = 0
    frames_dropped: int = 0
    total_bytes: int = 0
    latencies: List[float] = field(default_factory=list)
    start_time: float = 0.0
    errors: int = 0
    warmup_frames: int = 30


class GStreamerPipeline:
    """Manages a single GStreamer pipeline for video capture and encoding.
    
    This class handles:
    - Pipeline construction with automatic encoder detection
    - Video source handling (cameras, files, RTSP, HTTP)
    - Frame pulling from appsink
    - PTS-based latency measurement
    """
    
    def __init__(
        self,
        stream_key: str,
        source: Union[str, int],
        width: int,
        height: int,
        fps: int,
        config: GStreamerConfig,
    ):
        """Initialize GStreamer pipeline.

        Args:
            stream_key: Unique identifier for this stream
            source: Video source (camera index, file path, RTSP URL, etc.)
            width: Target output width
            height: Target output height
            fps: Target frames per second
            config: GStreamer configuration
        """
        self.stream_key = stream_key
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config

        self.logger = logging.getLogger(f"GStreamerPipeline-{stream_key}")

        self.pipeline = None
        self.appsink = None
        self.running = False

        # PTS-based latency tracking
        self.start_pts: Optional[int] = None
        self.wall_start_time: float = 0.0

        # Metrics
        self.metrics = GStreamerMetrics()
        self._metrics_lock = threading.Lock()

        # Detected encoder type
        self._encoder_type: Optional[str] = None

        # Platform detection and pipeline builder (NEW)
        from .device_detection import PlatformDetector
        from .platform_pipelines import PipelineFactory

        self.platform_detector = PlatformDetector.get_instance()
        self.platform_info = self.platform_detector.detect()
        self.pipeline_builder = PipelineFactory.get_builder(config, self.platform_info)
        
    def _detect_encoder(self) -> str:
        """Detect the best available encoder."""
        if self.config.encoder != "auto":
            return self.config.encoder
            
        # Try NVENC first (hardware)
        encoders_to_try = [
            ("nvenc", "nvh264enc ! fakesink"),
            ("x264", "x264enc ! fakesink"),
            ("openh264", "openh264enc ! fakesink"),
            ("jpeg", "jpegenc ! fakesink"),
        ]
        
        for encoder_name, test_pipeline_str in encoders_to_try:
            try:
                test_pipeline = Gst.parse_launch(test_pipeline_str)
                if test_pipeline:
                    test_pipeline.set_state(Gst.State.NULL)
                    self.logger.info(f"Detected available encoder: {encoder_name}")
                    return encoder_name
            except Exception:
                continue
                
        self.logger.warning("No hardware encoder found, falling back to x264")
        return "x264"
        
    def _detect_source_type(self) -> str:
        """Detect the type of video source."""
        source_str = str(self.source)
        
        if isinstance(self.source, int):
            return "v4l2"  # Linux camera
        elif source_str.startswith("rtsp://"):
            return "rtsp"
        elif source_str.startswith(("http://", "https://")):
            return "http"
        elif source_str.endswith((".mp4", ".avi", ".mkv", ".mov", ".webm")):
            return "file"
        else:
            # Assume it's a device path like /dev/video0
            return "v4l2"
            
    def _build_source_element(self) -> str:
        """Build GStreamer source element based on source type."""
        source_type = self._detect_source_type()
        
        if source_type == "v4l2":
            # Linux camera
            device = f"/dev/video{self.source}" if isinstance(self.source, int) else self.source
            return f"v4l2src device={device}"
            
        elif source_type == "rtsp":
            # RTSP stream with low-latency settings
            return (
                f"rtspsrc location={self.source} latency=100 buffer-mode=auto "
                f"! rtph264depay ! h264parse"
            )
            
        elif source_type == "http":
            # HTTP/HTTPS stream - use qtdemux for direct demuxing
            return f"souphttpsrc location={self.source} ! qtdemux ! avdec_h264"

        elif source_type == "file":
            # Video file - use qtdemux for mp4/mov, matroskademux for mkv
            # This avoids dynamic pad linking issues with decodebin
            ext = self.source.lower().split('.')[-1] if '.' in self.source else ''
            if ext in ('mp4', 'mov', 'm4v'):
                return f"filesrc location={self.source} ! qtdemux ! avdec_h264"
            elif ext in ('mkv', 'webm'):
                return f"filesrc location={self.source} ! matroskademux ! avdec_h264"
            elif ext in ('avi',):
                return f"filesrc location={self.source} ! avidemux ! avdec_h264"
            else:
                # Fallback to multifilesrc for unknown formats
                return f"filesrc location={self.source} ! qtdemux ! avdec_h264"
            
        else:
            # Default to videotestsrc for testing
            return "videotestsrc pattern=smpte is-live=true"
            
    def _build_encoder_element(self) -> tuple:
        """Build encoder element and output caps.
        
        Returns:
            Tuple of (encoder_string, output_caps)
        """
        encoder_type = self._detect_encoder()
        self._encoder_type = encoder_type
        bitrate_kbps = self.config.bitrate // 1000
        
        if encoder_type == "nvenc":
            # NVIDIA hardware encoder
            if self.config.codec == "h265":
                encoder = "nvh265enc"
            else:
                encoder = "nvh264enc"
                
            encoder_settings = (
                f"{encoder} "
                f"cuda-device-id={self.config.gpu_id} "
                f"preset={self.config.preset} "
                f"bitrate={bitrate_kbps} "
                f"gop-size={self.config.gop_size} "
                f"zerolatency=true "
                f"rc-lookahead=0 "
                f"bframes=0 "
                f"rc-mode=cbr-ld-hq "
            )
            caps_out = f"video/x-{self.config.codec},profile=main"
            
        elif encoder_type == "x264":
            # x264 software encoder - optimized for throughput
            threads = max(1, min(4, 8))  # Balance threads
            encoder_settings = (
                f"x264enc "
                f"speed-preset=ultrafast "
                f"tune=zerolatency "
                f"bitrate={bitrate_kbps} "
                f"key-int-max={self.config.gop_size} "
                f"bframes=0 "
                f"threads={threads} "
                f"sliced-threads=true "
                f"aud=false "
                f"cabac=false "
            )
            caps_out = "video/x-h264,profile=baseline"
            
        elif encoder_type == "openh264":
            # OpenH264 encoder
            encoder_settings = (
                f"openh264enc "
                f"bitrate={self.config.bitrate} "
                f"complexity=low "
                f"rate-control=bitrate "
            )
            caps_out = "video/x-h264,profile=baseline"
            
        elif encoder_type == "jpeg":
            # JPEG encoder - per-frame compression
            encoder_settings = (
                f"jpegenc "
                f"quality={self.config.jpeg_quality} "
                f"idct-method=ifast "
            )
            caps_out = "image/jpeg"
            
        else:
            raise RuntimeError(f"Unknown encoder type: {encoder_type}")
            
        return encoder_settings, caps_out
        
    def _build_pipeline_string(self) -> str:
        """Build platform-optimized GStreamer pipeline string."""
        # Detect source type
        source_type = self._detect_source_type()

        # Detect encoder (for compatibility)
        encoder = self._detect_encoder()
        self._encoder_type = encoder

        # Build config dict for pipeline builder
        builder_config = {
            'source_type': source_type,
            'source': self.source,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'encoder': encoder,
            'quality': self.config.jpeg_quality,
            'bitrate': self.config.bitrate,
        }

        # Use pipeline builder to construct platform-optimized pipeline
        if self.config.frame_optimizer_mode == "dual-appsink":
            pipeline_str = self.pipeline_builder.build_dual_appsink_pipeline(builder_config)
        else:
            pipeline_str = self.pipeline_builder.build_complete_pipeline(builder_config)

        if self.config.verbose_pipeline_logging:
            self.logger.info(f"Platform: {self.platform_info.platform_type.value}")
            self.logger.info(f"Encoder: {encoder}, Decoder: {self.platform_info.recommended_decoder}")
            self.logger.info(f"Pipeline: {pipeline_str[:200]}...")

        return pipeline_str
        
    def start(self) -> bool:
        """Start the GStreamer pipeline.

        Returns:
            bool: True if started successfully
        """
        if not GST_AVAILABLE:
            raise RuntimeError("GStreamer not available")

        if self.running:
            self.logger.warning("Pipeline already running")
            return False

        try:
            # Build and parse pipeline
            pipeline_str = self._build_pipeline_string()
            self.logger.info(f"Creating pipeline: {pipeline_str[:200]}...")

            self.pipeline = Gst.parse_launch(pipeline_str)

            # Get appsink (or appsinks for dual-appsink mode)
            self.appsink = self.pipeline.get_by_name("sink")
            if not self.appsink:
                # Try dual-appsink mode naming
                self.appsink = self.pipeline.get_by_name("output-sink")
            if not self.appsink:
                raise RuntimeError("Failed to get appsink from pipeline")

            # Setup bus for error handling
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message::error", self._on_error)
            bus.connect("message::warning", self._on_warning)
            bus.connect("message::eos", self._on_eos)

            # Start pipeline
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")

            # Wait for pipeline to be ready
            self.pipeline.get_state(Gst.CLOCK_TIME_NONE)

            self.running = True
            self.metrics.start_time = time.time()

            self.logger.info(
                f"Pipeline started - Platform: {self.platform_info.platform_type.value}, "
                f"Encoder: {self._encoder_type}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to start pipeline: {e}")

            # Fallback to CPU-only pipeline if enabled
            if self.config.fallback_on_error and self.config.platform != "cpu":
                self.logger.warning("Attempting fallback to CPU-only pipeline...")

                try:
                    # Force CPU-only pipeline
                    self.config.platform = "cpu"
                    from .platform_pipelines import PipelineFactory, CpuOnlyPipelineBuilder
                    self.pipeline_builder = CpuOnlyPipelineBuilder(self.config, self.platform_info)

                    # Retry with CPU pipeline
                    return self.start()

                except Exception as fallback_error:
                    self.logger.error(f"Fallback to CPU also failed: {fallback_error}")

            self.stop()
            raise
            
    def stop(self):
        """Stop the GStreamer pipeline."""
        self.running = False
        
        if self.pipeline:
            bus = self.pipeline.get_bus()
            if bus:
                bus.remove_signal_watch()
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            
        self.appsink = None
        self.logger.info("Pipeline stopped")
        
    def pull_frame(self, timeout_ns: int = None) -> Optional[tuple]:
        """Pull an encoded frame from the pipeline.

        Args:
            timeout_ns: Timeout in nanoseconds (default: 100ms)

        Returns:
            Tuple of (frame_data, latency_ms, size) or None if no frame
        """
        if not self.running or not self.appsink:
            return None

        timeout_ns = timeout_ns or (Gst.SECOND // 10)  # 100ms default for better compatibility
        
        try:
            sample = self.appsink.try_pull_sample(timeout_ns)
            if not sample:
                return None
                
            now = time.time()
            buffer = sample.get_buffer()
            
            # Get buffer data
            size = buffer.get_size()
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                return None
                
            # Copy frame data (buffer will be reused)
            frame_data = bytes(map_info.data)
            buffer.unmap(map_info)
            
            # Calculate latency using PTS
            pts = buffer.pts
            
            if self.start_pts is None:
                self.start_pts = pts
                self.wall_start_time = now
                
            latency_ms = 0.0
            with self._metrics_lock:
                self.metrics.frames_processed += 1
                self.metrics.total_bytes += size
                
                if (self.metrics.frames_processed > self.metrics.warmup_frames
                    and pts != Gst.CLOCK_TIME_NONE
                    and self.start_pts is not None):
                    
                    stream_time = (pts - self.start_pts) / Gst.SECOND
                    wall_time = now - self.wall_start_time
                    encode_latency = wall_time - stream_time
                    
                    if encode_latency >= 0:
                        latency_ms = encode_latency * 1000
                        self.metrics.latencies.append(encode_latency)
                    else:
                        latency_ms = 1.0  # Floor for early frames
                        self.metrics.latencies.append(0.001)
                        
            return frame_data, latency_ms, size
            
        except Exception as e:
            with self._metrics_lock:
                self.metrics.errors += 1
            self.logger.debug(f"Frame pull error: {e}")
            return None
            
    def get_metrics(self) -> GStreamerMetrics:
        """Get pipeline metrics."""
        with self._metrics_lock:
            return GStreamerMetrics(
                frames_processed=self.metrics.frames_processed,
                frames_dropped=self.metrics.frames_dropped,
                total_bytes=self.metrics.total_bytes,
                latencies=list(self.metrics.latencies[-100:]),  # Last 100
                start_time=self.metrics.start_time,
                errors=self.metrics.errors,
            )
            
    def _on_error(self, bus, message):
        """Handle pipeline errors."""
        err, debug = message.parse_error()
        self.logger.error(f"Pipeline error: {err}: {debug}")
        with self._metrics_lock:
            self.metrics.errors += 1
            
    def _on_warning(self, bus, message):
        """Handle pipeline warnings."""
        warn, debug = message.parse_warning()
        self.logger.warning(f"Pipeline warning: {warn}: {debug}")
        
    def _on_eos(self, bus, message):
        """Handle end-of-stream."""
        self.logger.info("End of stream received")


class GStreamerCameraStreamer:
    """GStreamer-based camera streamer with the same API as CameraStreamer.
    
    This class provides:
    - Same public API as CameraStreamer for drop-in replacement
    - GStreamer-based video capture and encoding
    - Support for hardware encoding (NVENC) when available
    - Multiple codec support (H.264, H.265, JPEG)
    - Robust retry logic and statistics tracking
    """
    
    def __init__(
        self,
        session,
        service_id: str,
        server_type: str,
        strip_input_content: bool = False,
        video_codec: Optional[str] = None,
        gateway_util: StreamingGatewayUtil = None,
        gstreamer_config: Optional[GStreamerConfig] = None,
        frame_optimizer_enabled: bool = True,
        frame_optimizer_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize GStreamerCameraStreamer.

        Args:
            session: Session object for authentication
            service_id: Deployment/gateway ID
            server_type: 'kafka' or 'redis'
            strip_input_content: Strip content for out-of-band retrieval
            video_codec: Video codec override
            gateway_util: Utility for API interactions
            gstreamer_config: GStreamer-specific configuration
            frame_optimizer_enabled: Enable frame optimization to skip similar frames
            frame_optimizer_config: Configuration for FrameOptimizer (scale, diff_threshold, etc.)
        """
        if not GST_AVAILABLE:
            raise RuntimeError(
                "GStreamer is not available. Please install GStreamer and PyGObject: "
                "pip install PyGObject && apt-get install gstreamer1.0-plugins-*"
            )

        self.session = session
        self.service_id = service_id
        self.server_type = server_type.lower()
        self.gateway_util = gateway_util
        self.gstreamer_config = gstreamer_config or GStreamerConfig()

        # Initialize GStreamer
        Gst.init(None)

        # Initialize modular components
        self.statistics = StreamStatistics()
        self.message_builder = StreamMessageBuilder(service_id, strip_input_content)

        # Initialize frame optimizer for skipping similar frames
        optimizer_config = frame_optimizer_config or {}
        self.frame_optimizer = FrameOptimizer(
            enabled=frame_optimizer_enabled,
            scale=optimizer_config.get("scale", 0.4),
            diff_threshold=optimizer_config.get("diff_threshold", 15),
            similarity_threshold=optimizer_config.get("similarity_threshold", 0.05),
            bg_update_interval=optimizer_config.get("bg_update_interval", 10),
        )
        self._last_sent_frame_ids: Dict[str, str] = {}  # stream_key -> last sent frame_id
        
        # Map video_codec to GStreamer config
        if video_codec:
            self._configure_codec(video_codec)
            
        # Pipeline management
        self.pipelines: Dict[str, GStreamerPipeline] = {}
        self.streaming_threads: List[threading.Thread] = []
        self._stop_streaming = False
        
        # Topic management
        self.stream_topics: Dict[str, str] = {}
        self.setup_topics = set()
        
        # Metrics logging
        self._last_metrics_log_time = time.time()
        self._metrics_log_interval = 30.0

        # Connection management (for refresh_connection_info support)
        self._connection_lock = threading.RLock()
        self._send_failure_count = 0
        self._last_connection_refresh_time = 0.0
        self.connection_refresh_threshold = 10  # Number of failures before refresh
        self.connection_refresh_interval = 60.0  # Minimum seconds between refreshes

        # Initialize MatriceStream
        if self.gateway_util:
            self.stream_config = self.gateway_util.get_and_wait_for_connection_info(
                server_type=self.server_type
            )
        else:
            self.stream_config = {}
            
        # Add Redis configuration
        if self.server_type == "redis":
            self.stream_config.update({
                'pool_max_connections': 500,
                'enable_batching': True,
                'batch_size': 10,
                'batch_timeout': 0.01
            })
            
        self.matrice_stream = MatriceStream(
            StreamType.REDIS if self.server_type == "redis" else StreamType.KAFKA,
            **self.stream_config
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"GStreamerCameraStreamer initialized - encoder: {self.gstreamer_config.encoder}, "
            f"codec: {self.gstreamer_config.codec}"
        )
        
    def _configure_codec(self, video_codec: str):
        """Configure GStreamer based on video codec string."""
        vc = video_codec.lower().strip()
        
        if vc in ("h264", "h264-frame"):
            self.gstreamer_config.codec = "h264"
        elif vc in ("h265", "h265-frame", "hevc"):
            self.gstreamer_config.codec = "h265"
        elif vc == "jpeg":
            self.gstreamer_config.encoder = "jpeg"
            
    # ========================================================================
    # Public API - Topic Management (same as CameraStreamer)
    # ========================================================================
    
    def register_stream_topic(self, stream_key: str, topic: str):
        """Register a topic for a specific stream key."""
        self.stream_topics[stream_key] = topic
        self.logger.info(f"Registered topic '{topic}' for stream '{stream_key}'")
        
    def get_topic_for_stream(self, stream_key: str) -> Optional[str]:
        """Get the topic for a specific stream key."""
        return self.stream_topics.get(stream_key)
        
    def setup_stream_for_topic(self, topic: str) -> bool:
        """Setup MatriceStream for a topic."""
        try:
            if topic not in self.setup_topics:
                self.matrice_stream.setup(topic)
                self.setup_topics.add(topic)
                self.logger.info(f"MatriceStream setup complete for topic: {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup MatriceStream for topic {topic}: {e}")
            return False
            
    # ========================================================================
    # Public API - Streaming Control
    # ========================================================================
    
    def start_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        simulate_video_file_stream: bool = False,
        is_video_chunk: bool = False,
        chunk_duration_seconds: Optional[float] = None,
        chunk_frames: Optional[int] = None,
        camera_location: Optional[str] = None,
    ) -> bool:
        """Start streaming in current thread (blocking)."""
        try:
            topic = self.get_topic_for_stream(stream_key)
            if not topic:
                self.logger.error(f"No topic registered for stream {stream_key}")
                return False
                
            self._stream_loop(
                input, stream_key or "default", stream_group_key or "default",
                topic, fps, quality, width or 640, height or 480,
                simulate_video_file_stream, camera_location or "Unknown"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}", exc_info=True)
            return False
            
    def start_background_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        simulate_video_file_stream: bool = False,
        is_video_chunk: bool = False,
        chunk_duration_seconds: Optional[float] = None,
        chunk_frames: Optional[int] = None,
        camera_location: Optional[str] = None,
    ) -> bool:
        """Start streaming in background thread (non-blocking)."""
        try:
            topic = self.get_topic_for_stream(stream_key)
            if not topic:
                self.logger.error(f"No topic registered for stream {stream_key}")
                return False
                
            thread = threading.Thread(
                target=self._stream_loop,
                args=(
                    input, stream_key or "default", stream_group_key or "default",
                    topic, fps, quality, width or 640, height or 480,
                    simulate_video_file_stream, camera_location or "Unknown"
                ),
                daemon=True
            )
            
            self.streaming_threads.append(thread)
            thread.start()
            self.logger.info(f"Started GStreamer background stream for {stream_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start background stream: {e}")
            return False
            
    def stop_streaming(self):
        """Stop all streaming threads and pipelines."""
        self._stop_streaming = True
        
        # Stop all pipelines
        for stream_key, pipeline in list(self.pipelines.items()):
            try:
                pipeline.stop()
            except Exception as e:
                self.logger.error(f"Error stopping pipeline {stream_key}: {e}")
        self.pipelines.clear()
        
        # Wait for threads
        for thread in self.streaming_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        self.streaming_threads.clear()
        
        self._stop_streaming = False
        self.logger.info("All GStreamer streams stopped")
        
    # ========================================================================
    # Public API - Statistics
    # ========================================================================
    
    def get_transmission_stats(self) -> Dict[str, Any]:
        """Get transmission statistics."""
        # Aggregate metrics from all pipelines
        total_frames = 0
        total_bytes = 0
        all_latencies = []
        total_errors = 0
        
        for pipeline in self.pipelines.values():
            metrics = pipeline.get_metrics()
            total_frames += metrics.frames_processed
            total_bytes += metrics.total_bytes
            all_latencies.extend(metrics.latencies)
            total_errors += metrics.errors
            
        stats = self.statistics.get_transmission_stats(
            f"gstreamer-{self.gstreamer_config.codec}",
            len(self.streaming_threads)
        )
        
        # Add GStreamer-specific stats
        stats["gstreamer"] = {
            "encoder": self.gstreamer_config.encoder,
            "codec": self.gstreamer_config.codec,
            "total_frames": total_frames,
            "total_bytes": total_bytes,
            "total_errors": total_errors,
            "avg_latency_ms": (
                sum(all_latencies) / len(all_latencies) * 1000
                if all_latencies else 0
            ),
        }
        
        return stats
        
    def reset_transmission_stats(self):
        """Reset transmission statistics."""
        self.statistics.reset()

    # ========================================================================
    # Public API - Message Production
    # ========================================================================

    def produce_request(
        self,
        input_data: bytes,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        metadata: Optional[Dict] = None,
        topic: Optional[str] = None,
        timeout: float = 60.0,
    ) -> bool:
        """Produce a stream request to MatriceStream (synchronous).

        Args:
            input_data: Frame data bytes
            stream_key: Stream identifier
            stream_group_key: Stream group identifier
            metadata: Optional metadata dictionary
            topic: Optional topic override
            timeout: Timeout in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            actual_topic = topic or self.get_topic_for_stream(stream_key) or "default_topic"
            metadata = metadata or {}

            last_read, last_write, last_process = self.statistics.get_timing(stream_key or "default")
            input_order = self.statistics.get_next_input_order(stream_key or "default")

            # Determine codec from metadata or config
            codec = metadata.get("video_codec") or ("jpeg" if self.gstreamer_config.encoder == "jpeg" else self.gstreamer_config.codec)

            message = self.message_builder.build_message(
                input_data, stream_key or "default", stream_group_key or "default",
                codec, metadata, actual_topic,
                self.matrice_stream.config.get('bootstrap_servers', 'localhost'),
                input_order, last_read, last_write, last_process
            )

            self.matrice_stream.add_message(
                topic_or_channel=actual_topic,
                message=message,
                key=str(stream_key)
            )

            self._send_failure_count = 0
            return True
        except Exception as e:
            self.logger.error(f"Failed to produce request: {e}")
            self._send_failure_count += 1
            return False

    async def async_produce_request(
        self,
        input_data: bytes,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        metadata: Optional[Dict] = None,
        topic: Optional[str] = None,
        timeout: float = 60.0,
    ) -> bool:
        """Produce a stream request to MatriceStream (asynchronous).

        Args:
            input_data: Frame data bytes
            stream_key: Stream identifier
            stream_group_key: Stream group identifier
            metadata: Optional metadata dictionary
            topic: Optional topic override
            timeout: Timeout in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            actual_topic = topic or self.get_topic_for_stream(stream_key) or "default_topic"
            metadata = metadata or {}

            last_read, last_write, last_process = self.statistics.get_timing(stream_key or "default")
            input_order = self.statistics.get_next_input_order(stream_key or "default")

            # Determine codec from metadata or config
            codec = metadata.get("video_codec") or ("jpeg" if self.gstreamer_config.encoder == "jpeg" else self.gstreamer_config.codec)

            message = self.message_builder.build_message(
                input_data, stream_key or "default", stream_group_key or "default",
                codec, metadata, actual_topic,
                self.matrice_stream.config.get('bootstrap_servers', 'localhost'),
                input_order, last_read, last_write, last_process
            )

            if not self.matrice_stream.is_async_setup():
                await self.matrice_stream.async_setup(actual_topic)

            await self.matrice_stream.async_add_message(
                topic_or_channel=actual_topic,
                message=message,
                key=str(stream_key)
            )

            self._send_failure_count = 0
            return True
        except Exception as e:
            self.logger.error(f"Failed to async produce request: {e}")
            self._send_failure_count += 1
            return False

    # ========================================================================
    # Public API - Connection Management
    # ========================================================================

    def refresh_connection_info(self) -> bool:
        """Refresh connection info from API and reinitialize MatriceStream.

        This method checks the server connection info from the API and if it has changed,
        it reinitializes the MatriceStream with the new connection details.

        Returns:
            bool: True if connection was refreshed successfully
        """
        if not self.gateway_util:
            self.logger.warning("Cannot refresh connection: no gateway_util provided")
            return False

        with self._connection_lock:
            current_time = time.time()

            # Check if enough time has passed since last refresh
            if current_time - self._last_connection_refresh_time < self.connection_refresh_interval:
                self.logger.debug(
                    f"Skipping connection refresh, last refresh was {current_time - self._last_connection_refresh_time:.1f}s ago"
                )
                return False

            try:
                self.logger.info("Attempting to refresh connection info from API...")

                # Fetch new connection info
                new_connection_info = self.gateway_util.get_and_wait_for_connection_info(
                    server_type=self.server_type,
                    connection_timeout=300
                )

                if not new_connection_info:
                    self.logger.error("Failed to fetch new connection info")
                    return False

                # Check if connection info has changed
                if new_connection_info == self.stream_config:
                    self.logger.info("Connection info unchanged, no refresh needed")
                    self._last_connection_refresh_time = current_time
                    return True

                self.logger.warning("Connection info has changed! Reinitializing MatriceStream...")

                # Close existing stream
                try:
                    self.matrice_stream.close()
                    self.logger.debug("Closed old MatriceStream connection")
                except Exception as e:
                    self.logger.warning(f"Error closing old stream: {e}")

                # Update config and reinitialize
                self.stream_config = new_connection_info

                # Add Redis batching config if needed
                if self.server_type == "redis":
                    self.stream_config.update({
                        'pool_max_connections': 500,
                        'enable_batching': True,
                        'batch_size': 10,
                        'batch_timeout': 0.01
                    })

                self.matrice_stream = MatriceStream(
                    StreamType.REDIS if self.server_type == "redis" else StreamType.KAFKA,
                    **self.stream_config
                )
                self.logger.info("MatriceStream reinitialized with new connection config")

                # Re-setup all topics
                topics_to_setup = list(self.setup_topics)
                self.setup_topics.clear()

                for topic in topics_to_setup:
                    try:
                        self.matrice_stream.setup(topic)
                        self.setup_topics.add(topic)
                        self.logger.info(f"Re-setup topic: {topic}")
                    except Exception as e:
                        self.logger.error(f"Failed to re-setup topic {topic}: {e}")

                # Reset failure count and update refresh time
                self._send_failure_count = 0
                self._last_connection_refresh_time = current_time

                self.logger.info("Connection info refreshed and MatriceStream reinitialized successfully!")
                return True

            except Exception as e:
                self.logger.error(f"Error refreshing connection info: {e}", exc_info=True)
                return False

    # ========================================================================
    # Private Methods - Main Streaming Loop
    # ========================================================================
    
    def _stream_loop(
        self,
        source: Union[str, int],
        stream_key: str,
        stream_group_key: str,
        topic: str,
        fps: int,
        quality: int,
        width: int,
        height: int,
        simulate_video_file_stream: bool,
        camera_location: str
    ):
        """Main streaming loop with GStreamer pipeline."""
        retry_mgr = RetryManager(stream_key)

        # Setup topic
        if not self.setup_stream_for_topic(topic):
            self.logger.error(f"Failed to setup topic {topic}")
            return

        # Detect source type for proper handling of video file end-of-stream
        source_str = str(source)
        is_video_file = source_str.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm'))
            
        # Configure JPEG quality if using JPEG encoder
        config = GStreamerConfig(
            encoder=self.gstreamer_config.encoder,
            codec=self.gstreamer_config.codec,
            bitrate=self.gstreamer_config.bitrate,
            preset=self.gstreamer_config.preset,
            gpu_id=self.gstreamer_config.gpu_id,
            use_cuda_memory=self.gstreamer_config.use_cuda_memory,
            jpeg_quality=quality,
            gop_size=self.gstreamer_config.gop_size,
        )
        
        # OUTER LOOP: Retry forever
        while not self._stop_streaming:
            pipeline = None
            
            try:
                # Create pipeline
                pipeline = GStreamerPipeline(
                    stream_key=stream_key,
                    source=source,
                    width=width,
                    height=height,
                    fps=fps,
                    config=config,
                )
                
                pipeline.start()
                self.pipelines[stream_key] = pipeline
                retry_mgr.handle_successful_reconnect()
                
                # INNER LOOP: Process frames
                frame_interval = 1.0 / fps
                
                while not self._stop_streaming:
                    loop_start = time.time()

                    # Check for EOS (End-of-Stream) from GStreamer bus
                    # This happens when video files reach the end
                    bus = pipeline.pipeline.get_bus()
                    if bus:
                        msg = bus.pop_filtered(Gst.MessageType.EOS)
                        if msg:
                            if is_video_file:
                                if simulate_video_file_stream:
                                    self.logger.info(
                                        f"Video {stream_key} reached end, restarting (simulate_video_file_stream=True)"
                                    )
                                    break  # Break inner loop to restart in outer loop
                                else:
                                    self.logger.info(
                                        f"Video {stream_key} playback complete (simulate_video_file_stream=False)"
                                    )
                                    return  # Exit streaming loop completely
                            else:
                                # Camera EOS is unexpected - treat as error
                                self.logger.warning(
                                    f"Unexpected EOS from camera {stream_key}, will reconnect"
                                )
                                break

                    # Pull encoded frame
                    read_start = time.time()
                    result = pipeline.pull_frame()
                    read_time = time.time() - read_start

                    if result is None:
                        retry_mgr.record_read_failure()
                        if retry_mgr.should_reconnect():
                            break
                        time.sleep(0.001)
                        continue

                    frame_data, latency_ms, frame_size = result
                    retry_mgr.record_success()

                    # Build and send message
                    self._process_and_send_frame(
                        frame_data, stream_key, stream_group_key, topic,
                        fps, quality, width, height, camera_location,
                        frame_size, latency_ms, read_time
                    )
                    
                    # Periodic metrics logging
                    self._maybe_log_metrics(stream_key)
                    
                    # Maintain FPS
                    elapsed = time.time() - loop_start
                    sleep_time = max(0, frame_interval - elapsed)
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                        
            except Exception as e:
                retry_mgr.handle_connection_failure(e)
                
            finally:
                if pipeline:
                    pipeline.stop()
                    if stream_key in self.pipelines:
                        del self.pipelines[stream_key]

            # Determine retry behavior based on source type and simulation flag
            if not self._stop_streaming:
                if is_video_file and simulate_video_file_stream:
                    # Video file with simulation enabled - restart immediately (no backoff)
                    self.logger.info(f"Restarting video {stream_key} immediately for continuous simulation")
                    time.sleep(0.1)  # Brief pause to allow cleanup
                    continue
                elif is_video_file and not simulate_video_file_stream:
                    # Video file without simulation - playback complete, exit cleanly
                    self.logger.info(f"Video {stream_key} playback complete (simulation disabled)")
                    break  # Exit outer loop
                else:
                    # Camera or RTSP stream - apply exponential backoff for reconnection
                    retry_mgr.wait_before_retry()

        self.logger.info(f"GStreamer stream ended for {stream_key}")
        
    def _process_and_send_frame(
        self,
        frame_data: bytes,
        stream_key: str,
        stream_group_key: str,
        topic: str,
        fps: int,
        quality: int,
        width: int,
        height: int,
        camera_location: str,
        frame_size: int,
        latency_ms: float,
        read_time: float
    ):
        """Build message and send to stream.

        NOTE: GStreamer frame optimization limitation:
        - For h264/h265 encoders: Frames are already encoded in pipeline, so similarity
          detection would require decoding (CPU overhead negates benefit)
        - For JPEG encoder: Could decode and use FrameOptimizer, but JPEG is already
          per-frame compression with no inter-frame dependencies
        - Future enhancement: Add dual appsink (one pre-encoder for similarity check)
        """
        # Get timing
        last_read, last_write, last_process = self.statistics.get_timing(stream_key)
        input_order = self.statistics.get_next_input_order(stream_key)

        # Check frame similarity using hash-based detection for video codecs
        # (Only effective for truly identical frames, not similar frames like FrameOptimizer)
        is_similar = False
        reference_frame_id = self._last_sent_frame_ids.get(stream_key)

        # Simple hash-based similarity for identical frames (basic optimization)
        if self.frame_optimizer.enabled and reference_frame_id:
            import hashlib
            frame_hash = hashlib.md5(frame_data).hexdigest()
            last_hash = getattr(self, '_last_frame_hashes', {}).get(stream_key)

            if last_hash == frame_hash:
                is_similar = True
            else:
                # Store new hash
                if not hasattr(self, '_last_frame_hashes'):
                    self._last_frame_hashes = {}
                self._last_frame_hashes[stream_key] = frame_hash

        # Build metadata (use build_frame_metadata for consistency)
        # Since we don't have video_props, create minimal metadata inline
        # TODO: Future enhancement - call build_frame_metadata with proper video_props
        metadata = {
            "source": stream_key,
            "fps": fps,
            "quality": quality,
            "width": width,
            "height": height,
            "camera_location": camera_location,
            "feed_type": "camera",
            "frame_count": 1,
            "stream_unit": "frame",
            "encoder": "gstreamer",
            "codec": self.gstreamer_config.codec,
            "encoding_latency_ms": latency_ms,
        }

        # Determine codec string for message
        codec = "jpeg" if self.gstreamer_config.encoder == "jpeg" else self.gstreamer_config.codec

        # If frame is identical to previous, send cached frame reference
        if is_similar and reference_frame_id:
            metadata["similarity_score"] = 1.0  # Hash-based, so exact match
            codec = "cached"
            frame_data_to_send = b""  # Empty content for cached frame
        else:
            frame_data_to_send = frame_data

        try:
            message = self.message_builder.build_message(
                frame_data=frame_data_to_send,
                stream_key=stream_key,
                stream_group_key=stream_group_key,
                codec=codec,
                metadata=metadata,
                topic=topic,
                broker_config=self.matrice_stream.config.get('bootstrap_servers', 'localhost'),
                input_order=input_order,
                last_read_time=last_read,
                last_write_time=last_write,
                last_process_time=last_process,
                cached_frame_id=reference_frame_id if is_similar else None,
            )

            write_start = time.time()
            self.matrice_stream.add_message(
                topic_or_channel=topic,
                message=message,
                key=str(stream_key)
            )
            write_time = time.time() - write_start

            # Track frame_id for future cached references
            if not is_similar:
                new_frame_id = message.get("frame_id")
                if new_frame_id:
                    self._last_sent_frame_ids[stream_key] = new_frame_id

            # Update statistics
            if is_similar:
                self.statistics.increment_frames_skipped()
                # For cached frames, frame_size is 0
                process_time = read_time + write_time
                self.statistics.update_timing(
                    stream_key, read_time, write_time, process_time,
                    0, 0  # No frame size or encoding time for cached
                )
            else:
                self.statistics.increment_frames_sent()
                process_time = read_time + write_time
                # Note: latency_ms is PTS-based pipeline latency, not pure encoding time
                # This is a known limitation - see Issue #15 in review
                self.statistics.update_timing(
                    stream_key, read_time, write_time, process_time,
                    frame_size, latency_ms / 1000
                )

        except Exception as e:
            self.logger.error(f"Failed to send frame for {stream_key}: {e}")
            
    def _maybe_log_metrics(self, stream_key: str):
        """Log comprehensive metrics if interval has elapsed."""
        current_time = time.time()
        if (current_time - self._last_metrics_log_time) >= self._metrics_log_interval:
            # Log detailed per-stream statistics
            self.statistics.log_detailed_stats(stream_key)

            # Log GStreamer-specific pipeline metrics
            if stream_key in self.pipelines:
                metrics = self.pipelines[stream_key].get_metrics()

                # Calculate statistics
                avg_latency = 0.0
                if metrics.latencies:
                    avg_latency = sum(metrics.latencies) / len(metrics.latencies) * 1000

                bandwidth_mbps = 0.0
                if metrics.total_bytes > 0 and current_time - metrics.start_time > 0:
                    duration = current_time - metrics.start_time
                    bandwidth_mbps = (metrics.total_bytes * 8) / (duration * 1_000_000)

                fps = 0.0
                if metrics.frames_processed > 0 and current_time - metrics.start_time > 0:
                    fps = metrics.frames_processed / (current_time - metrics.start_time)

                self.logger.info(
                    f"GStreamer [{stream_key}] Pipeline Metrics: "
                    f"encoder={self.gstreamer_config.encoder}, "
                    f"frames={metrics.frames_processed}, "
                    f"fps={fps:.1f}, "
                    f"errors={metrics.errors}, "
                    f"total_bytes={metrics.total_bytes / 1024 / 1024:.2f}MB, "
                    f"bandwidth={bandwidth_mbps:.2f}Mbps, "
                    f"avg_latency={avg_latency:.2f}ms"
                )

            # Log frame optimization metrics
            stats = self.statistics.get_transmission_stats(
                f"gstreamer-{self.gstreamer_config.encoder}",
                len(self.streaming_threads)
            )
            frames_sent = stats.get('frames_sent', 0)
            frames_skipped = stats.get('frames_skipped', 0)
            total_frames = frames_sent + frames_skipped

            if total_frames > 0:
                cache_efficiency = (frames_skipped / total_frames) * 100
                self.logger.info(
                    f"GStreamer [{stream_key}] Frame Optimization: "
                    f"sent={frames_sent}, "
                    f"cached={frames_skipped}, "
                    f"cache_efficiency={cache_efficiency:.1f}%, "
                    f"bandwidth_saved={(cache_efficiency):.1f}%"
                )

            self._last_metrics_log_time = current_time
            
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    async def close(self):
        """Clean up resources."""
        try:
            self.stop_streaming()
            await self.matrice_stream.async_close()
            self.matrice_stream.close()
            self.logger.info("GStreamerCameraStreamer closed")
        except Exception as e:
            self.logger.error(f"Error closing GStreamerCameraStreamer: {e}")


def is_gstreamer_available() -> bool:
    """Check if GStreamer is available on the system."""
    return GST_AVAILABLE

