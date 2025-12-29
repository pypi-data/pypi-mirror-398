"""GStreamer-based async camera worker process.

This module implements an async event loop worker that handles multiple cameras
using GStreamer pipelines for efficient hardware/software video encoding.
"""
import asyncio
import logging
import time
import multiprocessing
import os
import psutil
from typing import Dict, Any, Optional, List, Union
from collections import deque

from .message_builder import StreamMessageBuilder
from .stream_statistics import StreamStatistics

# Frame optimization
try:
    from matrice_common.optimize import FrameOptimizer
    FRAME_OPTIMIZER_AVAILABLE = True
except ImportError:
    FRAME_OPTIMIZER_AVAILABLE = False

# GStreamer imports (optional)
GST_AVAILABLE = False
try:
    import gi
    gi.require_version('Gst', '1.0')
    gi.require_version('GstApp', '1.0')
    from gi.repository import Gst, GstApp, GLib
    GST_AVAILABLE = True
except ImportError:
    pass


class GStreamerAsyncWorker:
    """Async worker process that handles multiple cameras using GStreamer.
    
    This worker runs an async event loop to manage GStreamer pipelines
    for multiple cameras with efficient encoding (NVENC/x264/JPEG).
    """
    
    def __init__(
        self,
        worker_id: int,
        camera_configs: List[Dict[str, Any]],
        stream_config: Dict[str, Any],
        stop_event: multiprocessing.Event,
        health_queue: multiprocessing.Queue,
        command_queue: Optional[multiprocessing.Queue] = None,
        response_queue: Optional[multiprocessing.Queue] = None,
        gstreamer_encoder: str = "auto",
        gstreamer_codec: str = "h264",
        gstreamer_preset: str = "low-latency",
        gpu_id: int = 0,
        # Platform-specific parameters
        platform: str = "auto",
        use_hardware_decode: bool = True,
        use_hardware_jpeg: bool = True,
        jetson_use_nvmm: bool = True,
        frame_optimizer_mode: str = "hash-only",
        fallback_on_error: bool = True,
        verbose_pipeline_logging: bool = False,
    ):
        """Initialize GStreamer async worker.

        Args:
            worker_id: Unique identifier for this worker
            camera_configs: List of camera configurations
            stream_config: Streaming configuration (Redis, Kafka, etc.)
            stop_event: Event to signal worker shutdown
            health_queue: Queue for reporting health status
            command_queue: Queue for receiving dynamic commands
            response_queue: Queue for sending responses
            gstreamer_encoder: Encoder type (auto, nvenc, x264, openh264, jpeg)
            gstreamer_codec: Codec (h264, h265)
            gstreamer_preset: NVENC preset
            gpu_id: GPU device ID for NVENC
            platform: Platform override (auto, jetson, desktop-gpu, intel, amd, cpu)
            use_hardware_decode: Enable hardware decode
            use_hardware_jpeg: Enable hardware JPEG encoding
            jetson_use_nvmm: Use NVMM zero-copy on Jetson
            frame_optimizer_mode: Frame optimization mode
            fallback_on_error: Fallback to CPU on errors
            verbose_pipeline_logging: Enable verbose logging
        """
        if not GST_AVAILABLE:
            raise RuntimeError("GStreamer not available for GStreamerAsyncWorker")
            
        self.worker_id = worker_id
        self.camera_configs = camera_configs
        self.stream_config = stream_config
        self.stop_event = stop_event
        self.health_queue = health_queue
        self.command_queue = command_queue
        self.response_queue = response_queue
        
        # GStreamer settings
        self.gstreamer_encoder = gstreamer_encoder
        self.gstreamer_codec = gstreamer_codec
        self.gstreamer_preset = gstreamer_preset
        self.gpu_id = gpu_id
        
        # Logging
        self.logger = logging.getLogger(f"GStreamerWorker-{worker_id}")
        self.logger.info(f"Initializing GStreamer worker {worker_id} with {len(camera_configs)} cameras")

        # Initialize GStreamer
        Gst.init(None)

        # Platform detection and pipeline builder (NEW)
        from .device_detection import PlatformDetector
        from .platform_pipelines import PipelineFactory
        from .gstreamer_camera_streamer import GStreamerConfig

        # Build GStreamerConfig from worker settings
        self.gstreamer_config = GStreamerConfig(
            encoder=gstreamer_encoder,
            codec=gstreamer_codec,
            preset=gstreamer_preset,
            gpu_id=gpu_id,
            platform=platform,
            use_hardware_decode=use_hardware_decode,
            use_hardware_jpeg=use_hardware_jpeg,
            jetson_use_nvmm=jetson_use_nvmm,
            frame_optimizer_mode=frame_optimizer_mode,
            fallback_on_error=fallback_on_error,
            verbose_pipeline_logging=verbose_pipeline_logging,
        )

        self.platform_detector = PlatformDetector.get_instance()
        self.platform_info = self.platform_detector.detect()
        self.pipeline_builder = PipelineFactory.get_builder(self.gstreamer_config, self.platform_info)

        self.logger.info(
            f"Worker {worker_id}: Platform={self.platform_info.platform_type.value}, "
            f"Recommended encoder={self.platform_info.recommended_encoder}"
        )

        # Components
        self.message_builder = StreamMessageBuilder(
            service_id=stream_config.get('service_id', 'streaming_gateway'),
            strip_input_content=False
        )
        self.statistics = StreamStatistics()

        # Initialize frame optimizer for skipping similar frames (hash-based for GStreamer)
        if FRAME_OPTIMIZER_AVAILABLE:
            self.frame_optimizer = FrameOptimizer(
                enabled=True,
                scale=0.4,
                diff_threshold=15,
                similarity_threshold=0.05,
                bg_update_interval=10,
            )
        else:
            self.frame_optimizer = None
        self._last_sent_frame_ids: Dict[str, str] = {}  # stream_key -> last sent frame_id
        self._last_frame_hashes: Dict[str, str] = {}  # stream_key -> frame hash for similarity

        # Pipeline management
        self.camera_tasks: Dict[str, asyncio.Task] = {}
        self.pipelines: Dict[str, Any] = {}  # GStreamer pipelines

        # Redis client
        self.redis_client = None

        # Metrics
        self._encoding_times = deque(maxlen=100)
        self._frame_times = deque(maxlen=100)
        self._frames_encoded = 0
        self._encoding_errors = 0
        self._last_metrics_log = time.time()
        self._metrics_log_interval = 30.0
        self._process_info = psutil.Process(os.getpid())

        # Detected encoder
        self._detected_encoder: Optional[str] = None

        self.logger.info(
            f"GStreamer Worker {worker_id}: encoder={gstreamer_encoder}, "
            f"codec={gstreamer_codec}, gpu_id={gpu_id}"
        )
        
    def _detect_encoder(self) -> str:
        """Detect the best available encoder."""
        if self.gstreamer_encoder != "auto":
            return self.gstreamer_encoder
            
        encoders = [
            ("nvenc", "nvh264enc ! fakesink"),
            ("x264", "x264enc ! fakesink"),
            ("openh264", "openh264enc ! fakesink"),
            ("jpeg", "jpegenc ! fakesink"),
        ]
        
        for name, test_str in encoders:
            try:
                test = Gst.parse_launch(test_str)
                if test:
                    test.set_state(Gst.State.NULL)
                    self.logger.info(f"Detected encoder: {name}")
                    return name
            except Exception:
                continue
                
        return "x264"
        
    def _build_pipeline_string(
        self,
        source: Union[str, int],
        width: int,
        height: int,
        fps: int,
        quality: int = 85
    ) -> str:
        """Build platform-optimized GStreamer pipeline string.

        Args:
            source: Video source
            width: Target width
            height: Target height
            fps: Target FPS
            quality: JPEG quality (for jpeg encoder)

        Returns:
            Pipeline description string
        """
        # Detect source type
        source_str = str(source)
        if isinstance(source, int):
            source_type = "camera"
        elif source_str.startswith("rtsp://"):
            source_type = "rtsp"
        elif source_str.startswith(("http://", "https://")):
            source_type = "http"
        elif source_str.endswith((".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi")):
            source_type = "file"
        else:
            source_type = "camera"

        # Detect encoder
        encoder_type = self._detected_encoder or self._detect_encoder()
        self._detected_encoder = encoder_type

        # Build config dict for pipeline builder
        builder_config = {
            'source_type': source_type,
            'source': source,
            'width': width,
            'height': height,
            'fps': fps,
            'encoder': encoder_type,
            'quality': quality,
            'bitrate': 4000000,  # 4 Mbps
        }

        # Use pipeline builder to construct platform-optimized pipeline
        if self.gstreamer_config.frame_optimizer_mode == "dual-appsink":
            pipeline_str = self.pipeline_builder.build_dual_appsink_pipeline(builder_config)
        else:
            pipeline_str = self.pipeline_builder.build_complete_pipeline(builder_config)

        if self.gstreamer_config.verbose_pipeline_logging:
            self.logger.info(f"Worker {self.worker_id} Pipeline: {pipeline_str[:150]}...")

        return pipeline_str
        
    async def initialize(self):
        """Initialize async resources."""
        try:
            from matrice_common.stream import MatriceStream, StreamType
            
            self.stream = MatriceStream(
                stream_type=StreamType.REDIS,
                **self.stream_config
            )
            
            self.redis_client = self.stream.async_client
            await self.redis_client.setup_client()
            
            self.logger.info(f"Worker {self.worker_id}: Initialized async Redis client")
            
        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Failed to initialize: {exc}", exc_info=True)
            raise
            
    async def run(self):
        """Main worker loop."""
        try:
            await self.initialize()
            
            # Start camera tasks
            for camera_config in self.camera_configs:
                await self._add_camera_internal(camera_config)
                
            self._report_health("running", len(self.camera_tasks))
            
            # Start command handler
            command_task = None
            if self.command_queue:
                command_task = asyncio.create_task(
                    self._command_handler(),
                    name="command-handler"
                )
                
            # Monitor loop
            while not self.stop_event.is_set():
                # Check tasks
                for stream_key, task in list(self.camera_tasks.items()):
                    if task.done():
                        try:
                            task.result()
                        except Exception as exc:
                            self.logger.error(f"Camera {stream_key} failed: {exc}")
                        del self.camera_tasks[stream_key]
                        
                self._report_health("running", len(self.camera_tasks))
                await asyncio.sleep(1.0)
                
            # Shutdown
            if command_task and not command_task.done():
                command_task.cancel()
                try:
                    await command_task
                except asyncio.CancelledError:
                    pass
                    
            await self._shutdown()
            
        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Fatal error: {exc}", exc_info=True)
            self._report_health("error", error=str(exc))
            raise
            
    async def _camera_handler(self, camera_config: Dict[str, Any]):
        """Handle a single camera with GStreamer pipeline.

        Args:
            camera_config: Camera configuration
        """
        stream_key = camera_config['stream_key']
        stream_group_key = camera_config.get('stream_group_key', 'default')
        source = camera_config['source']
        topic = camera_config['topic']
        fps = camera_config.get('fps', 30)
        quality = camera_config.get('quality', 85)
        width = camera_config.get('width', 640)
        height = camera_config.get('height', 480)
        camera_location = camera_config.get('camera_location', 'Unknown')
        simulate_video_file_stream = camera_config.get('simulate_video_file_stream', False)

        # Retry settings
        MIN_RETRY_COOLDOWN = 5
        MAX_RETRY_COOLDOWN = 30
        retry_cycle = 0

        # Detect source type for proper handling of video file end-of-stream
        source_str = str(source)
        is_video_file = source_str.endswith(('.mp4', '.avi', '.mkv', '.mov', '.webm'))

        # Track if we've successfully warmed up once (for faster restarts)
        has_warmed_up_once = False

        # OUTER LOOP: Retry forever
        while not self.stop_event.is_set():
            pipeline = None
            appsink = None
            start_pts = None
            wall_start_time = 0.0
            consecutive_failures = 0
            frame_counter = 0

            try:
                # Build and start pipeline
                pipeline_str = self._build_pipeline_string(source, width, height, fps, quality)
                if not has_warmed_up_once:
                    self.logger.info(f"Worker {self.worker_id}: Starting pipeline for {stream_key}")

                pipeline = Gst.parse_launch(pipeline_str)
                appsink = pipeline.get_by_name("sink")

                if not appsink:
                    raise RuntimeError("Failed to get appsink")

                # Start pipeline
                ret = pipeline.set_state(Gst.State.PLAYING)
                if ret == Gst.StateChangeReturn.FAILURE:
                    raise RuntimeError("Failed to start pipeline")

                pipeline.get_state(Gst.CLOCK_TIME_NONE)

                self.pipelines[stream_key] = pipeline
                retry_cycle = 0

                if not has_warmed_up_once:
                    self.logger.info(
                        f"Worker {self.worker_id}: Camera {stream_key} started - "
                        f"{width}x{height} @ {fps} FPS (encoder: {self._detected_encoder})"
                    )

                # Wait for first frame (warmup)
                # First time: longer timeout with initial delay
                # Subsequent restarts: fast path with no delay
                warmup_start = time.time()
                warmup_success = False
                first_sample = None

                if has_warmed_up_once:
                    # Fast path for video loop restarts - no delay, shorter timeout
                    warmup_timeout = 2.0
                    warmup_attempts = 0
                    while time.time() - warmup_start < warmup_timeout:
                        if self.stop_event.is_set():
                            break
                        warmup_attempts += 1
                        try:
                            first_sample = await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: appsink.try_pull_sample(Gst.SECOND // 5)  # 200ms timeout
                            )
                        except Exception:
                            first_sample = None
                        if first_sample:
                            warmup_success = True
                            break
                        await asyncio.sleep(0.02)  # Very short delay between attempts
                else:
                    # First time warmup - longer timeout with initial delay
                    warmup_timeout = 10.0
                    await asyncio.sleep(0.1)  # Brief initial delay

                    warmup_attempts = 0
                    while time.time() - warmup_start < warmup_timeout:
                        if self.stop_event.is_set():
                            break

                        warmup_attempts += 1

                        # Check for errors on the bus first
                        bus = pipeline.get_bus()
                        if bus:
                            error_msg = bus.pop_filtered(Gst.MessageType.ERROR)
                            if error_msg:
                                err, debug = error_msg.parse_error()
                                raise RuntimeError(f"Pipeline error during warmup: {err.message}")

                        # Try to pull first sample with 500ms timeout
                        try:
                            first_sample = await asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: appsink.try_pull_sample(Gst.SECOND // 2)  # 500ms timeout
                            )
                        except Exception as pull_err:
                            self.logger.debug(f"Warmup pull attempt {warmup_attempts} failed: {pull_err}")
                            first_sample = None

                        if first_sample:
                            self.logger.info(
                                f"Worker {self.worker_id}: Pipeline {stream_key} warmed up "
                                f"in {time.time() - warmup_start:.2f}s (attempt {warmup_attempts})"
                            )
                            warmup_success = True
                            has_warmed_up_once = True
                            break

                        # Short delay between attempts
                        await asyncio.sleep(0.1)

                if not warmup_success and not self.stop_event.is_set():
                    if not has_warmed_up_once:
                        self.logger.warning(
                            f"Worker {self.worker_id}: Pipeline {stream_key} warmup failed after "
                            f"{warmup_attempts} attempts ({time.time() - warmup_start:.2f}s)"
                        )
                    raise RuntimeError(f"Pipeline failed to produce frames within {warmup_timeout}s")

                # Process the first frame pulled during warmup
                if first_sample and not self.stop_event.is_set():
                    buffer = first_sample.get_buffer()
                    size = buffer.get_size()

                    success, map_info = buffer.map(Gst.MapFlags.READ)
                    if success:
                        frame_data = bytes(map_info.data)
                        buffer.unmap(map_info)

                        # Initialize PTS tracking
                        start_pts = buffer.pts
                        wall_start_time = time.time()
                        frame_counter = 1

                        # Send first frame
                        await self._process_and_send_frame(
                            frame_data, stream_key, stream_group_key, topic,
                            fps, quality, width, height, camera_location,
                            size, 0.0, frame_counter, 0.0
                        )

                # INNER LOOP: Process frames
                frame_interval = 1.0 / fps

                while not self.stop_event.is_set():
                    try:
                        loop_start = time.time()

                        # Check for EOS (End-of-Stream) from GStreamer bus
                        # This happens when video files reach the end
                        bus = pipeline.get_bus()
                        if bus:
                            msg = bus.pop_filtered(Gst.MessageType.EOS)
                            if msg:
                                if is_video_file:
                                    if simulate_video_file_stream:
                                        self.logger.info(
                                            f"Worker {self.worker_id}: Video {stream_key} reached end, "
                                            f"restarting (simulate_video_file_stream=True)"
                                        )
                                        await asyncio.sleep(1.0)
                                        break  # Restart in outer loop
                                    else:
                                        self.logger.info(
                                            f"Worker {self.worker_id}: Video {stream_key} playback complete "
                                            f"(simulate_video_file_stream=False)"
                                        )
                                        return  # Exit completely
                                else:
                                    # Camera EOS is unexpected - treat as error
                                    self.logger.warning(
                                        f"Worker {self.worker_id}: Unexpected EOS from camera {stream_key}, "
                                        f"will reconnect"
                                    )
                                    consecutive_failures += 1
                                    if consecutive_failures >= 10:
                                        break

                        # Pull frame (with timeout)
                        read_start = time.time()
                        sample = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: appsink.try_pull_sample(Gst.SECOND // 10)  # 100ms timeout
                        )
                        read_time = time.time() - read_start

                        if not sample:
                            consecutive_failures += 1

                            # Note: EOS handling is done above via bus messages
                            # This section handles frame read failures (network issues, etc.)
                            if consecutive_failures >= 10:
                                if is_video_file:
                                    self.logger.info(
                                        f"Worker {self.worker_id}: Video {stream_key} - "
                                        f"no frames available, restarting"
                                    )
                                else:
                                    self.logger.warning(
                                        f"Worker {self.worker_id}: Camera {stream_key} - "
                                        f"reconnecting after {consecutive_failures} failures"
                                    )
                                break

                            await asyncio.sleep(0.01)
                            continue

                        consecutive_failures = 0
                        frame_counter += 1

                        now = time.time()
                        buffer = sample.get_buffer()
                        size = buffer.get_size()

                        # Get frame data
                        success, map_info = buffer.map(Gst.MapFlags.READ)
                        if not success:
                            continue
                        frame_data = bytes(map_info.data)
                        buffer.unmap(map_info)

                        # Calculate latency using PTS
                        pts = buffer.pts
                        latency_ms = 0.0

                        if start_pts is None:
                            start_pts = pts
                            wall_start_time = now

                        if pts != Gst.CLOCK_TIME_NONE and start_pts is not None:
                            stream_time = (pts - start_pts) / Gst.SECOND
                            wall_time = now - wall_start_time
                            encode_latency = wall_time - stream_time
                            latency_ms = max(0, encode_latency * 1000)

                        # Track metrics
                        self._frames_encoded += 1
                        self._encoding_times.append(latency_ms / 1000)

                        # Send frame
                        await self._process_and_send_frame(
                            frame_data, stream_key, stream_group_key, topic,
                            fps, quality, width, height, camera_location,
                            size, latency_ms, frame_counter, read_time
                        )
                        
                        # Log metrics periodically
                        if time.time() - self._last_metrics_log > self._metrics_log_interval:
                            self._last_metrics_log = time.time()
                            await self._log_metrics()
                            
                        # Maintain FPS
                        elapsed = time.time() - loop_start
                        sleep_time = max(0, frame_interval - elapsed)
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)
                            
                    except asyncio.CancelledError:
                        return
                    except Exception as exc:
                        self.logger.error(f"Frame error in {stream_key}: {exc}")
                        consecutive_failures += 1
                        if consecutive_failures >= 10:
                            break
                        await asyncio.sleep(0.1)
                        
            except asyncio.CancelledError:
                return
            except Exception as exc:
                self.logger.error(f"Pipeline error for {stream_key}: {exc}", exc_info=True)
                self._encoding_errors += 1
                
            finally:
                if pipeline:
                    pipeline.set_state(Gst.State.NULL)
                if stream_key in self.pipelines:
                    del self.pipelines[stream_key]

            # Determine retry behavior based on source type and simulation flag
            if self.stop_event.is_set():
                break

            if is_video_file and simulate_video_file_stream:
                # Video file with simulation enabled - restart immediately (no backoff)
                self.logger.info(
                    f"Worker {self.worker_id}: Restarting video {stream_key} immediately "
                    f"for continuous simulation"
                )
                continue  # Restart immediately
            elif is_video_file and not simulate_video_file_stream:
                # Video file without simulation - playback complete, exit cleanly
                self.logger.info(
                    f"Worker {self.worker_id}: Video {stream_key} playback complete "
                    f"(simulation disabled)"
                )
                break  # Exit outer loop
            else:
                # Camera or RTSP stream - apply exponential backoff for reconnection
                cooldown = min(MAX_RETRY_COOLDOWN, MIN_RETRY_COOLDOWN + retry_cycle)
                self.logger.info(f"Worker {self.worker_id}: Retrying camera {stream_key} in {cooldown}s")
                await asyncio.sleep(cooldown)
                retry_cycle += 1

        self.logger.info(f"Worker {self.worker_id}: Camera handler for {stream_key} exited")
        
    async def _process_and_send_frame(
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
        frame_counter: int,
        read_time: float
    ):
        """Build and send frame message to Redis.

        NOTE: GStreamer frame optimization uses hash-based similarity for identical frames.
        See gstreamer_camera_streamer.py for detailed explanation of limitations.
        """
        last_read, last_write, last_process = self.statistics.get_timing(stream_key)
        input_order = self.statistics.get_next_input_order(stream_key)

        # Check frame similarity using hash-based detection (identical frames only)
        is_similar = False
        reference_frame_id = self._last_sent_frame_ids.get(stream_key)

        if self.frame_optimizer and reference_frame_id:
            import hashlib
            frame_hash = hashlib.md5(frame_data).hexdigest()
            last_hash = self._last_frame_hashes.get(stream_key)

            if last_hash == frame_hash:
                is_similar = True
            else:
                self._last_frame_hashes[stream_key] = frame_hash

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
            "encoder": f"gstreamer-{self._detected_encoder}",
            "codec": self.gstreamer_codec,
            "encoding_latency_ms": latency_ms,
            "frame_number": frame_counter,
        }

        # If frame is identical, send cached reference
        if is_similar and reference_frame_id:
            metadata["similarity_score"] = 1.0
            codec = "cached"
            frame_data_to_send = b""
        else:
            codec = "jpeg" if self._detected_encoder == "jpeg" else self.gstreamer_codec
            frame_data_to_send = frame_data

        message = self.message_builder.build_message(
            frame_data=frame_data_to_send,
            stream_key=stream_key,
            stream_group_key=stream_group_key,
            codec=codec,
            metadata=metadata,
            topic=topic,
            broker_config=self.stream_config.get('bootstrap_servers', 'localhost'),
            input_order=input_order,
            last_read_time=last_read,
            last_write_time=last_write,
            last_process_time=last_process,
            cached_frame_id=reference_frame_id if is_similar else None,
        )

        write_start = time.time()
        await self.redis_client.add_message(topic, message)
        write_time = time.time() - write_start

        # Track frame_id for future cached references
        if not is_similar:
            new_frame_id = message.get("frame_id")
            if new_frame_id:
                self._last_sent_frame_ids[stream_key] = new_frame_id

        # Update statistics
        if is_similar:
            self.statistics.increment_frames_skipped()
            process_time = read_time + write_time
            self.statistics.update_timing(
                stream_key, read_time, write_time, process_time,
                0, 0  # No frame size or encoding time for cached
            )
        else:
            self.statistics.increment_frames_sent()
            process_time = read_time + write_time
            # Note: latency_ms is PTS-based, not pure encoding time
            self.statistics.update_timing(
                stream_key, read_time, write_time, process_time,
                frame_size, latency_ms / 1000
            )

        total_frame_time = write_time + (latency_ms / 1000)
        self._frame_times.append(total_frame_time)
        
    async def _log_metrics(self):
        """Log worker metrics."""
        try:
            # Per-camera
            for stream_key in self.camera_tasks.keys():
                self.statistics.log_detailed_stats(stream_key)
                
            # Worker-level
            if self._encoding_times:
                avg_ms = sum(self._encoding_times) / len(self._encoding_times) * 1000
                self.logger.info(
                    f"Worker {self.worker_id} GStreamer: "
                    f"encoder={self._detected_encoder}, "
                    f"frames={self._frames_encoded}, "
                    f"errors={self._encoding_errors}, "
                    f"avg_latency={avg_ms:.2f}ms"
                )
                
            # Resources
            cpu = self._process_info.cpu_percent(interval=0.1)
            mem = self._process_info.memory_info().rss / 1024 / 1024
            self.logger.info(
                f"Worker {self.worker_id} Resources: CPU={cpu:.1f}%, Memory={mem:.1f}MB"
            )
            
        except Exception as exc:
            self.logger.warning(f"Failed to log metrics: {exc}")
            
    async def _command_handler(self):
        """Process commands from manager."""
        while not self.stop_event.is_set():
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, self._get_command_nonblocking
                )
                
                if command:
                    await self._process_command(command)
                else:
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error(f"Command handler error: {exc}")
                await asyncio.sleep(1.0)
                
    def _get_command_nonblocking(self):
        """Get command without blocking."""
        try:
            return self.command_queue.get_nowait()
        except Exception:
            return None
            
    async def _process_command(self, command: Dict[str, Any]):
        """Process a command."""
        cmd_type = command.get('type')
        self.logger.info(f"Processing command: {cmd_type}")
        
        try:
            if cmd_type == 'add_camera':
                camera_config = command.get('camera_config')
                success = await self._add_camera_internal(camera_config)
                self._send_response(cmd_type, camera_config.get('stream_key'), success)
                
            elif cmd_type == 'remove_camera':
                stream_key = command.get('stream_key')
                success = await self._remove_camera_internal(stream_key)
                self._send_response(cmd_type, stream_key, success)
                
            elif cmd_type == 'update_camera':
                camera_config = command.get('camera_config')
                stream_key = command.get('stream_key')
                await self._remove_camera_internal(stream_key)
                success = await self._add_camera_internal(camera_config)
                self._send_response(cmd_type, stream_key, success)
                
        except Exception as exc:
            self.logger.error(f"Error processing {cmd_type}: {exc}")
            self._send_response(cmd_type, command.get('stream_key'), False, str(exc))
            
    async def _add_camera_internal(self, camera_config: Dict[str, Any]) -> bool:
        """Add camera and start task."""
        stream_key = camera_config.get('stream_key')
        
        if not stream_key:
            return False
            
        if stream_key in self.camera_tasks:
            self.logger.warning(f"Camera {stream_key} already exists")
            return False
            
        try:
            task = asyncio.create_task(
                self._camera_handler(camera_config),
                name=f"gst-camera-{stream_key}"
            )
            self.camera_tasks[stream_key] = task
            self.logger.info(f"Added GStreamer camera {stream_key}")
            return True
            
        except Exception as exc:
            self.logger.error(f"Failed to add camera {stream_key}: {exc}")
            return False
            
    async def _remove_camera_internal(self, stream_key: str) -> bool:
        """Remove camera and stop task."""
        if stream_key not in self.camera_tasks:
            return False
            
        try:
            task = self.camera_tasks[stream_key]
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                    
            del self.camera_tasks[stream_key]
            
            if stream_key in self.pipelines:
                self.pipelines[stream_key].set_state(Gst.State.NULL)
                del self.pipelines[stream_key]
                
            self.logger.info(f"Removed camera {stream_key}")
            return True
            
        except Exception as exc:
            self.logger.error(f"Error removing {stream_key}: {exc}")
            return False
            
    def _send_response(self, cmd_type: str, stream_key: str, success: bool, error: str = None):
        """Send response to manager."""
        if self.response_queue:
            try:
                self.response_queue.put_nowait({
                    'worker_id': self.worker_id,
                    'command_type': cmd_type,
                    'stream_key': stream_key,
                    'success': success,
                    'error': error,
                    'timestamp': time.time()
                })
            except Exception as exc:
                self.logger.warning(f"Failed to send response: {exc}")
                
    async def _shutdown(self):
        """Graceful shutdown."""
        self.logger.info(f"Worker {self.worker_id}: Shutting down")
        
        # Cancel tasks
        for stream_key, task in self.camera_tasks.items():
            if not task.done():
                task.cancel()
                
        if self.camera_tasks:
            await asyncio.gather(*self.camera_tasks.values(), return_exceptions=True)
            
        # Stop pipelines
        for stream_key, pipeline in list(self.pipelines.items()):
            pipeline.set_state(Gst.State.NULL)
        self.pipelines.clear()
        
        # Close Redis
        if self.redis_client:
            await self.redis_client.close()
            
        self._report_health("stopped")
        self.logger.info(f"Worker {self.worker_id}: Shutdown complete")
        
    def _report_health(self, status: str, active_cameras: int = 0, error: Optional[str] = None):
        """Report health status."""
        try:
            cpu = 0
            mem = 0
            try:
                cpu = self._process_info.cpu_percent(interval=None)
                mem = self._process_info.memory_info().rss / 1024 / 1024
            except Exception:
                pass
                
            avg_encoding_ms = 0
            if self._encoding_times:
                avg_encoding_ms = sum(self._encoding_times) / len(self._encoding_times) * 1000
                
            health_report = {
                'worker_id': self.worker_id,
                'status': status,
                'active_cameras': active_cameras,
                'timestamp': time.time(),
                'error': error,
                'worker_type': 'gstreamer',
                'encoder': self._detected_encoder,
                'metrics': {
                    'cpu_percent': cpu,
                    'memory_mb': mem,
                    'frames_encoded': self._frames_encoded,
                    'encoding_errors': self._encoding_errors,
                    'avg_encoding_ms': avg_encoding_ms,
                },
            }
            self.health_queue.put_nowait(health_report)
            
        except Exception as exc:
            self.logger.warning(f"Failed to report health: {exc}")


def run_gstreamer_worker(
    worker_id: int,
    camera_configs: List[Dict[str, Any]],
    stream_config: Dict[str, Any],
    stop_event: multiprocessing.Event,
    health_queue: multiprocessing.Queue,
    command_queue: multiprocessing.Queue = None,
    response_queue: multiprocessing.Queue = None,
    gstreamer_encoder: str = "auto",
    gstreamer_codec: str = "h264",
    gstreamer_preset: str = "low-latency",
    gpu_id: int = 0,
    platform: str = "auto",
    use_hardware_decode: bool = True,
    use_hardware_jpeg: bool = True,
    jetson_use_nvmm: bool = True,
    frame_optimizer_mode: str = "hash-only",
    fallback_on_error: bool = True,
    verbose_pipeline_logging: bool = False,
):
    """Entry point for GStreamer worker process.

    Args:
        worker_id: Worker identifier
        camera_configs: Camera configurations
        stream_config: Streaming configuration
        stop_event: Shutdown event
        health_queue: Health reporting queue
        command_queue: Command queue
        response_queue: Response queue
        gstreamer_encoder: Encoder type
        gstreamer_codec: Codec
        gstreamer_preset: NVENC preset
        gpu_id: GPU device ID
        platform: Platform override
        use_hardware_decode: Enable hardware decode
        use_hardware_jpeg: Enable hardware JPEG
        jetson_use_nvmm: Use NVMM on Jetson
        frame_optimizer_mode: Frame optimization mode
        fallback_on_error: Fallback to CPU on errors
        verbose_pipeline_logging: Verbose logging
    """
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - GStreamerWorker-{worker_id} - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(f"GStreamerWorker-{worker_id}")
    logger.info(f"Starting GStreamer worker {worker_id}")
    
    try:
        worker = GStreamerAsyncWorker(
            worker_id=worker_id,
            camera_configs=camera_configs,
            stream_config=stream_config,
            stop_event=stop_event,
            health_queue=health_queue,
            command_queue=command_queue,
            response_queue=response_queue,
            gstreamer_encoder=gstreamer_encoder,
            gstreamer_codec=gstreamer_codec,
            gstreamer_preset=gstreamer_preset,
            gpu_id=gpu_id,
            platform=platform,
            use_hardware_decode=use_hardware_decode,
            use_hardware_jpeg=use_hardware_jpeg,
            jetson_use_nvmm=jetson_use_nvmm,
            frame_optimizer_mode=frame_optimizer_mode,
            fallback_on_error=fallback_on_error,
            verbose_pipeline_logging=verbose_pipeline_logging,
        )
        
        asyncio.run(worker.run())
        
    except Exception as exc:
        logger.error(f"Worker {worker_id} failed: {exc}", exc_info=True)
        raise


def is_gstreamer_available() -> bool:
    """Check if GStreamer is available."""
    return GST_AVAILABLE

