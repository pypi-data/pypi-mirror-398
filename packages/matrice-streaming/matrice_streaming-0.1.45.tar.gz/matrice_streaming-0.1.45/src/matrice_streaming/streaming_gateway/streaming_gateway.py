import logging
import base64
import time
import threading
import atexit
from typing import Dict, List, Optional, Any
from .camera_streamer import CameraStreamer
from .camera_streamer.worker_manager import WorkerManager
from .streaming_gateway_utils import (
    StreamingGatewayUtil,
    InputStream,
    input_stream_to_camera_config,
    build_stream_config,
)
from .event_listener import EventListener
from .dynamic_camera_manager import DynamicCameraManager, DynamicCameraManagerForWorkers

# GStreamer imports (optional - graceful degradation)
GSTREAMER_AVAILABLE = False
try:
    from .camera_streamer.gstreamer_camera_streamer import (
        GStreamerCameraStreamer,
        GStreamerConfig,
        is_gstreamer_available,
    )
    from .camera_streamer.gstreamer_worker_manager import GStreamerWorkerManager
    GSTREAMER_AVAILABLE = is_gstreamer_available()
except (ImportError, ValueError):
    # ImportError: gi module not available
    # ValueError: gi.require_version fails when GStreamer not installed
    pass


class StreamingGateway:
    """Simplified streaming gateway for managing camera streams."""

    # Class-level tracking of active instances
    _active_instances: Dict[str, "StreamingGateway"] = {}
    _class_lock = threading.RLock()

    def __init__(
        self,
        session,
        streaming_gateway_id: str = None,
        server_id: str = None,
        server_type: str = None,
        inputs_config: List[InputStream] = None,
        video_codec: Optional[str] = None,
        force_restart: bool = False,
        enable_event_listening: bool = True,
        action_id: str = None,
        use_async_workers: bool = True,
        num_workers: int = None,  # Auto-calculate based on CPU cores and camera count
        max_cameras_per_worker: int = 50,
        allow_empty_start: bool = True,
        # GStreamer options
        use_gstreamer: bool = False,
        gstreamer_encoder: str = "auto",  # auto, nvenc, x264, openh264, jpeg
        gstreamer_codec: str = "h264",  # h264, h265
        gstreamer_preset: str = "low-latency",  # NVENC preset
        gstreamer_gpu_id: int = 0,  # GPU device ID for NVENC
        # Platform-specific GStreamer options
        gstreamer_platform: str = "auto",  # auto, jetson, desktop-gpu, intel, amd, cpu
        gstreamer_use_hardware_decode: bool = True,  # Use hardware decode (nvv4l2decoder, nvdec, vaapi)
        gstreamer_use_hardware_jpeg: bool = True,  # Use hardware JPEG (nvjpegenc, vaapijpegenc)
        gstreamer_jetson_use_nvmm: bool = True,  # Use NVMM zero-copy on Jetson
        gstreamer_frame_optimizer_mode: str = "hash-only",  # hash-only, dual-appsink, disabled
        gstreamer_fallback_on_error: bool = True,  # Gracefully fallback to CPU pipeline on error
        gstreamer_verbose_logging: bool = False,  # Verbose pipeline logging for debugging
    ):
        """Initialize StreamingGateway.

        Args:
            session: Session object for authentication
            streaming_gateway_id: ID of the streaming gateway
            server_id: ID of the server (Kafka/Redis)
            server_type: Type of server (kafka or redis)
            inputs_config: List of InputStream configurations
            video_codec: Video codec (h264 or h265)
            force_restart: Force stop existing streams and restart
            enable_event_listening: Enable dynamic event listening for configuration updates
            action_id: Optional action ID to pass in API requests
            use_async_workers: Use new async worker flow (default True)
            num_workers: Number of worker processes for async flow
            max_cameras_per_worker: Maximum cameras per worker process
            allow_empty_start: Allow starting with zero cameras (default True)
            use_gstreamer: Use GStreamer-based encoding (default False)
            gstreamer_encoder: GStreamer encoder type (auto, nvenc, x264, openh264, jpeg)
            gstreamer_codec: GStreamer codec (h264, h265)
            gstreamer_preset: NVENC preset for hardware encoding
            gstreamer_gpu_id: GPU device ID for NVENC hardware encoding
            gstreamer_platform: Platform override (auto, jetson, desktop-gpu, intel, amd, cpu)
            gstreamer_use_hardware_decode: Enable hardware decode (nvv4l2decoder, nvdec, vaapi)
            gstreamer_use_hardware_jpeg: Enable hardware JPEG encoding when available
            gstreamer_jetson_use_nvmm: Use NVMM zero-copy memory on Jetson devices
            gstreamer_frame_optimizer_mode: Frame optimization mode (hash-only, dual-appsink, disabled)
            gstreamer_fallback_on_error: Automatically fallback to CPU pipeline on hardware errors
            gstreamer_verbose_logging: Enable verbose pipeline construction logging
        """
        if not session:
            raise ValueError("Session is required")
        if not streaming_gateway_id:
            raise ValueError("streaming_gateway_id is required")

        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.force_restart = force_restart
        self.enable_event_listening = enable_event_listening
        self.use_async_workers = use_async_workers
        self.num_workers = num_workers
        self.max_cameras_per_worker = max_cameras_per_worker
        self.video_codec = video_codec
        
        # GStreamer configuration
        self.use_gstreamer = use_gstreamer
        self.gstreamer_encoder = gstreamer_encoder
        self.gstreamer_codec = gstreamer_codec
        self.gstreamer_preset = gstreamer_preset
        self.gstreamer_gpu_id = gstreamer_gpu_id
        # Platform-specific GStreamer configuration
        self.gstreamer_platform = gstreamer_platform
        self.gstreamer_use_hardware_decode = gstreamer_use_hardware_decode
        self.gstreamer_use_hardware_jpeg = gstreamer_use_hardware_jpeg
        self.gstreamer_jetson_use_nvmm = gstreamer_jetson_use_nvmm
        self.gstreamer_frame_optimizer_mode = gstreamer_frame_optimizer_mode
        self.gstreamer_fallback_on_error = gstreamer_fallback_on_error
        self.gstreamer_verbose_logging = gstreamer_verbose_logging
        
        # Validate GStreamer availability if requested
        if use_gstreamer and not GSTREAMER_AVAILABLE:
            raise RuntimeError(
                "GStreamer requested but not available. "
                "Install with: pip install PyGObject && apt-get install gstreamer1.0-plugins-*"
            )

        # Initialize utility for API interactions
        self.gateway_util = StreamingGatewayUtil(session, streaming_gateway_id, server_id, action_id=action_id)

        # Determine server_type - fetch from API if not provided
        if server_type is None:
            gateway_info = self.gateway_util.get_streaming_gateway_by_id()
            if gateway_info:
                server_type = gateway_info.get('serverType')
                logging.info(f"Retrieved server_type from API: {server_type}")
            else:
                raise ValueError("server_type is required but could not be retrieved from API")

        if not server_type:
            raise ValueError("server_type is required (kafka or redis)")

        self.server_type = server_type
        self.allow_empty_start = allow_empty_start

        # Get input configurations
        if inputs_config is None:
            logging.info("Fetching input configurations from API")
            try:
                self.inputs_config = self.gateway_util.get_input_streams()
            except Exception as exc:
                logging.warning(f"Failed to fetch cameras from API: {exc}")
                if allow_empty_start:
                    logging.info("Continuing with zero cameras (allow_empty_start=True)")
                    self.inputs_config = []
                else:
                    raise
        else:
            self.inputs_config = inputs_config if isinstance(inputs_config, list) else [inputs_config]

        # Check if we have cameras
        if not self.inputs_config:
            if allow_empty_start:
                logging.warning("Starting gateway with zero cameras - use camera_manager.add_camera() to add dynamically")
            else:
                raise ValueError("No input configurations available and allow_empty_start=False")

        # Validate inputs (only if we have any)
        for i, config in enumerate(self.inputs_config):
            if not isinstance(config, InputStream):
                raise ValueError(f"Input config {i} must be an InputStream instance")

        # Initialize streaming backend based on configuration
        # Options: use_gstreamer (GStreamer-based), use_async_workers (AsyncCameraWorker), or CameraStreamer
        self.camera_streamer: Optional[CameraStreamer] = None
        self.worker_manager: Optional[WorkerManager] = None
        self.gstreamer_streamer: Optional[Any] = None  # GStreamerCameraStreamer
        self.gstreamer_worker_manager: Optional[Any] = None  # GStreamerWorkerManager

        if self.use_gstreamer:
            # GStreamer-based encoding flow
            if self.use_async_workers:
                # GStreamer with worker processes
                logging.info(
                    f"Initializing GStreamer worker flow - encoder: {gstreamer_encoder}, "
                    f"codec: {gstreamer_codec}, gpu: {gstreamer_gpu_id}"
                )

                # Build stream config for workers
                stream_config = build_stream_config(
                    gateway_util=self.gateway_util,
                    server_type=server_type,
                    service_id=streaming_gateway_id,
                )

                # Convert InputStream configs to camera_config dicts
                camera_configs = [
                    input_stream_to_camera_config(inp) for inp in self.inputs_config
                ]

                self.gstreamer_worker_manager = GStreamerWorkerManager(
                    camera_configs=camera_configs,
                    stream_config=stream_config,
                    num_workers=num_workers,
                    max_cameras_per_worker=max_cameras_per_worker,
                    gstreamer_encoder=gstreamer_encoder,
                    gstreamer_codec=gstreamer_codec,
                    gstreamer_preset=gstreamer_preset,
                    gpu_id=gstreamer_gpu_id,
                    platform=gstreamer_platform,
                    use_hardware_decode=gstreamer_use_hardware_decode,
                    use_hardware_jpeg=gstreamer_use_hardware_jpeg,
                    jetson_use_nvmm=gstreamer_jetson_use_nvmm,
                    frame_optimizer_mode=gstreamer_frame_optimizer_mode,
                    fallback_on_error=gstreamer_fallback_on_error,
                    verbose_pipeline_logging=gstreamer_verbose_logging,
                )

                # Initialize dynamic camera manager for GStreamer workers
                # Use the same interface as WorkerManager
                self.camera_manager = DynamicCameraManagerForWorkers(
                    worker_manager=self.gstreamer_worker_manager,
                    streaming_gateway_id=streaming_gateway_id,
                    session=self.session,
                    streaming_gateway=self,
                )
            else:
                # GStreamer single-threaded mode
                logging.info(
                    f"Initializing GStreamer CameraStreamer - encoder: {gstreamer_encoder}, "
                    f"codec: {gstreamer_codec}, gpu: {gstreamer_gpu_id}"
                )

                gst_config = GStreamerConfig(
                    encoder=gstreamer_encoder,
                    codec=gstreamer_codec,
                    preset=gstreamer_preset,
                    gpu_id=gstreamer_gpu_id,
                    platform=gstreamer_platform,
                    use_hardware_decode=gstreamer_use_hardware_decode,
                    use_hardware_jpeg=gstreamer_use_hardware_jpeg,
                    jetson_use_nvmm=gstreamer_jetson_use_nvmm,
                    frame_optimizer_mode=gstreamer_frame_optimizer_mode,
                    fallback_on_error=gstreamer_fallback_on_error,
                    verbose_pipeline_logging=gstreamer_verbose_logging,
                )

                self.gstreamer_streamer = GStreamerCameraStreamer(
                    session=self.session,
                    service_id=streaming_gateway_id,
                    server_type=server_type,
                    video_codec=video_codec,
                    gateway_util=self.gateway_util,
                    gstreamer_config=gst_config,
                )

                # Initialize dynamic camera manager for GStreamer streamer
                # GStreamerCameraStreamer has the same API as CameraStreamer
                self.camera_manager = DynamicCameraManager(
                    camera_streamer=self.gstreamer_streamer,
                    streaming_gateway_id=streaming_gateway_id,
                    session=self.session,
                    streaming_gateway=self,
                )

        elif self.use_async_workers:
            # New async worker flow using WorkerManager
            logging.info("Initializing async worker flow with WorkerManager")

            # Build stream config for workers
            stream_config = build_stream_config(
                gateway_util=self.gateway_util,
                server_type=server_type,
                service_id=streaming_gateway_id,
            )

            # Convert InputStream configs to camera_config dicts
            camera_configs = [
                input_stream_to_camera_config(inp) for inp in self.inputs_config
            ]

            self.worker_manager = WorkerManager(
                camera_configs=camera_configs,
                stream_config=stream_config,
                num_workers=num_workers,
                max_cameras_per_worker=max_cameras_per_worker,
            )

            # Initialize dynamic camera manager for workers
            self.camera_manager = DynamicCameraManagerForWorkers(
                worker_manager=self.worker_manager,
                streaming_gateway_id=streaming_gateway_id,
                session=self.session,
                streaming_gateway=self,
            )
        else:
            # Original CameraStreamer flow
            logging.info("Initializing original CameraStreamer flow")
            self.camera_streamer = CameraStreamer(
                session=self.session,
                service_id=streaming_gateway_id,
                server_type=server_type,
                video_codec=video_codec,
                gateway_util=self.gateway_util,
            )

            # Initialize dynamic camera manager for CameraStreamer
            self.camera_manager = DynamicCameraManager(
                camera_streamer=self.camera_streamer,
                streaming_gateway_id=streaming_gateway_id,
                session=self.session,
                streaming_gateway=self,
            )

        # Initialize with current camera configurations
        self.camera_manager.initialize_from_config(self.inputs_config)

        # Initialize event system (if enabled)
        self.event_listener: Optional[EventListener] = None
        
        if self.enable_event_listening:
            try:
                self.event_listener = EventListener(
                    session=self.session,
                    streaming_gateway_id=self.streaming_gateway_id,
                    camera_manager=self.camera_manager
                )
            except Exception as e:
                logging.warning(f"Could not initialize event system: {e}")
                logging.info("Continuing without event listening")

        # State management
        self.is_streaming = False
        self._stop_event = threading.Event()
        self._state_lock = threading.RLock()
        self._my_stream_keys = set()
        self._stream_key_to_camera_id = {}  # Mapping of stream_key -> camera_id
        self._cleanup_registered = False

        # Statistics
        self.stats = {
            "start_time": None,
            "current_status": "initialized",
        }

        # Register cleanup handler to ensure status is updated on unexpected shutdown
        atexit.register(self._emergency_cleanup)
        self._cleanup_registered = True

        logging.info(f"StreamingGateway initialized for {self.streaming_gateway_id}")

    def _register_as_active(self):
        """Register this instance as active."""
        with self.__class__._class_lock:
            self.__class__._active_instances[self.streaming_gateway_id] = self
        logging.info(f"Registered as active: {self.streaming_gateway_id}")

    def _unregister_as_active(self):
        """Unregister this instance from active tracking."""
        with self.__class__._class_lock:
            if self.streaming_gateway_id in self.__class__._active_instances:
                if self.__class__._active_instances[self.streaming_gateway_id] is self:
                    del self.__class__._active_instances[self.streaming_gateway_id]
        logging.info(f"Unregistered: {self.streaming_gateway_id}")

    def _stop_existing_streams(self):
        """Stop existing streams if force_restart is enabled."""
        if not self.force_restart:
            return

        logging.warning(f"Force stopping existing streams for {self.streaming_gateway_id}")

        with self.__class__._class_lock:
            if self.streaming_gateway_id in self.__class__._active_instances:
                existing_instance = self.__class__._active_instances[self.streaming_gateway_id]
                try:
                    existing_instance.stop_streaming()
                    logging.info(f"Force stopped existing streams for {self.streaming_gateway_id}")
                except Exception as e:
                    logging.warning(f"Error during force stop: {e}")
                time.sleep(1.0)

    def start_streaming(self) -> bool:
        """Start streaming.

        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        with self._state_lock:
            if self.is_streaming:
                logging.warning("Streaming is already active")
                return False

        # Check if we have cameras (allow empty if flag is set)
        if not self.inputs_config:
            if self.allow_empty_start:
                logging.warning("Starting streaming with zero cameras - awaiting dynamic camera addition")
            else:
                logging.error("No input configurations available")
                return False

        # Force stop existing streams if requested
        self._stop_existing_streams()

        # Register as active
        self._register_as_active()

        try:
            if self.use_gstreamer:
                if self.use_async_workers:
                    success = self._start_gstreamer_worker_streaming()
                else:
                    success = self._start_gstreamer_streamer_streaming()
            elif self.use_async_workers:
                success = self._start_async_worker_streaming()
            else:
                success = self._start_camera_streamer_streaming()

            if not success:
                return False

            with self._state_lock:
                self._stop_event.clear()
                self.is_streaming = True
                self.stats["start_time"] = time.time()
                self.stats["current_status"] = "running"

            # Start event listener if enabled
            if self.event_listener and not self.event_listener.is_listening:
                logging.info("Starting event listener for dynamic updates")
                self.event_listener.start()

            logging.info(f"Started streaming with {len(self.inputs_config)} inputs")
            return True

        except Exception as exc:
            logging.error(f"Error starting streaming: {exc}", exc_info=True)
            try:
                self.stop_streaming()
            except Exception as cleanup_exc:
                logging.error(f"Error during cleanup: {cleanup_exc}")
            return False

    def _start_async_worker_streaming(self) -> bool:
        """Start streaming using new async worker flow.

        Returns:
            bool: True if started successfully, False otherwise
        """
        num_cameras = len(self.inputs_config) if self.inputs_config else 0
        logging.info(f"Starting async worker streaming flow with {num_cameras} cameras")

        # Build stream key mappings (if we have cameras)
        if self.inputs_config:
            for i, input_config in enumerate(self.inputs_config):
                stream_key = input_config.camera_key or f"stream_{i}"
                camera_id = input_config.camera_id or stream_key
                self._stream_key_to_camera_id[stream_key] = camera_id
                self._my_stream_keys.add(stream_key)

        # Start the worker manager (this starts all worker processes)
        # WorkerManager handles empty camera lists gracefully
        try:
            self.worker_manager.start()
            logging.info(f"Started WorkerManager with {self.num_workers} workers, {num_cameras} cameras")
            return True
        except Exception as exc:
            logging.error(f"Failed to start WorkerManager: {exc}", exc_info=True)
            return False

    def _start_camera_streamer_streaming(self) -> bool:
        """Start streaming using original CameraStreamer flow.

        Returns:
            bool: True if started successfully, False otherwise
        """
        num_cameras = len(self.inputs_config) if self.inputs_config else 0
        logging.info(f"Starting CameraStreamer streaming flow with {num_cameras} cameras")

        # If no cameras, just return success (infrastructure is ready for dynamic cameras)
        if not self.inputs_config:
            logging.info("No cameras to start - awaiting dynamic camera addition")
            return True

        started_streams = []

        for i, input_config in enumerate(self.inputs_config):
            stream_key = input_config.camera_key or f"stream_{i}"

            # Store camera_id mapping for metrics
            camera_id = input_config.camera_id or stream_key
            self._stream_key_to_camera_id[stream_key] = camera_id

            # Register topic - generate default if not provided
            topic = input_config.camera_input_topic
            if not topic:
                # Generate default topic name
                topic = f"{camera_id}_input_topic"
                logging.warning(f"No input topic for camera {input_config.camera_key}, using default: {topic}")

            self.camera_streamer.register_stream_topic(stream_key, topic)

            # Start streaming
            success = self.camera_streamer.start_background_stream(
                input=input_config.source,
                fps=input_config.fps,
                stream_key=stream_key,
                stream_group_key=input_config.camera_group_key,
                quality=input_config.quality,
                width=input_config.width,
                height=input_config.height,
                simulate_video_file_stream=input_config.simulate_video_file_stream,
                camera_location=input_config.camera_location,
            )

            if not success:
                logging.error(f"Failed to start streaming for {input_config.source}")
                if started_streams:
                    logging.info("Stopping already started streams")
                    self.stop_streaming()
                return False

            started_streams.append(stream_key)
            self._my_stream_keys.add(stream_key)
            logging.info(f"Started streaming for camera: {input_config.camera_key}")

        return True

    def _start_gstreamer_worker_streaming(self) -> bool:
        """Start streaming using GStreamer worker processes.

        Returns:
            bool: True if started successfully, False otherwise
        """
        num_cameras = len(self.inputs_config) if self.inputs_config else 0
        logging.info(
            f"Starting GStreamer worker streaming with {num_cameras} cameras "
            f"(encoder: {self.gstreamer_encoder}, codec: {self.gstreamer_codec})"
        )

        # Build stream key mappings
        if self.inputs_config:
            for i, input_config in enumerate(self.inputs_config):
                stream_key = input_config.camera_key or f"stream_{i}"
                camera_id = input_config.camera_id or stream_key
                self._stream_key_to_camera_id[stream_key] = camera_id
                self._my_stream_keys.add(stream_key)

        # Start the GStreamer worker manager
        try:
            self.gstreamer_worker_manager.start()
            logging.info(
                f"Started GStreamerWorkerManager with {self.num_workers} workers, "
                f"{num_cameras} cameras"
            )
            return True
        except Exception as exc:
            logging.error(f"Failed to start GStreamerWorkerManager: {exc}", exc_info=True)
            return False

    def _start_gstreamer_streamer_streaming(self) -> bool:
        """Start streaming using GStreamer CameraStreamer (single-threaded).

        Returns:
            bool: True if started successfully, False otherwise
        """
        num_cameras = len(self.inputs_config) if self.inputs_config else 0
        logging.info(
            f"Starting GStreamer CameraStreamer with {num_cameras} cameras "
            f"(encoder: {self.gstreamer_encoder}, codec: {self.gstreamer_codec})"
        )

        # If no cameras, return success (ready for dynamic cameras)
        if not self.inputs_config:
            logging.info("No cameras to start - awaiting dynamic camera addition")
            return True

        started_streams = []

        for i, input_config in enumerate(self.inputs_config):
            stream_key = input_config.camera_key or f"stream_{i}"

            # Store camera_id mapping
            camera_id = input_config.camera_id or stream_key
            self._stream_key_to_camera_id[stream_key] = camera_id

            # Register topic
            topic = input_config.camera_input_topic
            if not topic:
                topic = f"{camera_id}_input_topic"
                logging.warning(f"No input topic for camera {input_config.camera_key}, using default: {topic}")

            self.gstreamer_streamer.register_stream_topic(stream_key, topic)

            # Start streaming
            success = self.gstreamer_streamer.start_background_stream(
                input=input_config.source,
                fps=input_config.fps,
                stream_key=stream_key,
                stream_group_key=input_config.camera_group_key,
                quality=input_config.quality,
                width=input_config.width,
                height=input_config.height,
                simulate_video_file_stream=input_config.simulate_video_file_stream,
                camera_location=input_config.camera_location,
            )

            if not success:
                logging.error(f"Failed to start GStreamer streaming for {input_config.source}")
                if started_streams:
                    logging.info("Stopping already started streams")
                    self.stop_streaming()
                return False

            started_streams.append(stream_key)
            self._my_stream_keys.add(stream_key)
            logging.info(f"Started GStreamer streaming for camera: {input_config.camera_key}")

        return True

    def stop_streaming(self):
        """Stop all streaming operations."""
        with self._state_lock:
            if not self.is_streaming:
                logging.warning("Streaming is not active")
                return

            logging.info("Stopping streaming...")
            self._stop_event.set()
            self.is_streaming = False
            self.stats["current_status"] = "stopped"

        # Stop event listener first
        if self.event_listener and self.event_listener.is_listening:
            logging.info("Stopping event listener")
            try:
                self.event_listener.stop()
            except Exception as exc:
                logging.error(f"Error stopping event listener: {exc}")

        # Stop streaming backend based on which flow is active
        if self.use_gstreamer:
            # Stop GStreamer backends
            if self.use_async_workers:
                # Stop GStreamerWorkerManager
                if self.gstreamer_worker_manager:
                    try:
                        logging.info("Stopping GStreamerWorkerManager")
                        self.gstreamer_worker_manager.stop()
                        # Reset statistics for clean restart
                        logging.info("Resetting GStreamer worker manager statistics")
                    except Exception as exc:
                        logging.error(f"Error stopping GStreamerWorkerManager: {exc}")
            else:
                # Stop GStreamerCameraStreamer
                if self.gstreamer_streamer:
                    try:
                        logging.info("Stopping GStreamerCameraStreamer")
                        self.gstreamer_streamer.stop_streaming()
                        # Reset statistics for clean restart
                        self.gstreamer_streamer.reset_transmission_stats()
                        # Clear pipeline references
                        if hasattr(self.gstreamer_streamer, 'pipelines'):
                            self.gstreamer_streamer.pipelines.clear()
                        # Join streaming threads with timeout
                        if hasattr(self.gstreamer_streamer, 'streaming_threads'):
                            for thread in self.gstreamer_streamer.streaming_threads:
                                if thread.is_alive():
                                    thread.join(timeout=5.0)
                            self.gstreamer_streamer.streaming_threads.clear()
                        logging.info("GStreamer cleanup completed")
                    except Exception as exc:
                        logging.error(f"Error stopping GStreamer streaming: {exc}")
        elif self.use_async_workers:
            # Stop WorkerManager
            if self.worker_manager:
                try:
                    logging.info("Stopping WorkerManager")
                    self.worker_manager.stop()
                except Exception as exc:
                    logging.error(f"Error stopping WorkerManager: {exc}")
        else:
            # Stop CameraStreamer
            if self.camera_streamer:
                try:
                    self.camera_streamer.stop_streaming()
                except Exception as exc:
                    logging.error(f"Error stopping camera streaming: {exc}")

        # Always attempt to update status to "stopped", even if other steps fail
        # This is critical for proper gateway lifecycle management
        status_updated = False
        try:
            self.gateway_util.stop_streaming()
        except Exception as exc:
            logging.error(f"Error calling stop_streaming API: {exc}")

        try:
            # Update status to "stopped" - this should always succeed
            self.gateway_util.update_status("stopped")
            status_updated = True
            logging.info("Gateway status updated to 'stopped'")
        except Exception as exc:
            logging.error(f"CRITICAL: Failed to update gateway status to 'stopped': {exc}")
            logging.error("This may cause issues with gateway lifecycle tracking")

        # Unregister
        self._unregister_as_active()

        # Clear stream keys
        self._my_stream_keys.clear()

        # Unregister atexit handler since we've successfully cleaned up
        if self._cleanup_registered:
            try:
                atexit.unregister(self._emergency_cleanup)
                self._cleanup_registered = False
            except Exception:
                pass

        logging.info(f"Streaming stopped (status updated: {status_updated})")

    def get_camera_id_for_stream_key(self, stream_key: str) -> Optional[str]:
        """Get camera_id for a given stream_key."""
        return self._stream_key_to_camera_id.get(stream_key)

    def get_statistics(self) -> Dict:
        """Get streaming statistics."""
        with self._state_lock:
            stats = self.stats.copy()

        if stats["start_time"]:
            stats["runtime_seconds"] = time.time() - stats["start_time"]
        else:
            stats["runtime_seconds"] = 0

        stats["is_streaming"] = self.is_streaming
        stats["my_stream_keys"] = list(self._my_stream_keys)
        stats["stream_key_to_camera_id"] = self._stream_key_to_camera_id.copy()
        stats["event_listening_enabled"] = self.enable_event_listening
        stats["use_async_workers"] = self.use_async_workers
        stats["use_gstreamer"] = self.use_gstreamer

        # Add backend-specific statistics
        if self.use_gstreamer:
            # GStreamer statistics
            stats["gstreamer_config"] = {
                "encoder": self.gstreamer_encoder,
                "codec": self.gstreamer_codec,
                "preset": self.gstreamer_preset,
                "gpu_id": self.gstreamer_gpu_id,
                "platform": self.gstreamer_platform,
                "use_hardware_decode": self.gstreamer_use_hardware_decode,
                "use_hardware_jpeg": self.gstreamer_use_hardware_jpeg,
                "jetson_use_nvmm": self.gstreamer_jetson_use_nvmm,
                "frame_optimizer_mode": self.gstreamer_frame_optimizer_mode,
                "fallback_on_error": self.gstreamer_fallback_on_error,
                "verbose_logging": self.gstreamer_verbose_logging,
            }
            if self.use_async_workers:
                # GStreamerWorkerManager statistics
                if self.gstreamer_worker_manager:
                    try:
                        stats["worker_stats"] = self.gstreamer_worker_manager.get_worker_statistics()
                        stats["camera_assignments"] = self.gstreamer_worker_manager.get_camera_assignments()
                    except Exception as exc:
                        logging.warning(f"Failed to get GStreamer worker stats: {exc}")
            else:
                # GStreamerCameraStreamer statistics
                if self.gstreamer_streamer:
                    try:
                        stats["transmission_stats"] = self.gstreamer_streamer.get_transmission_stats()
                    except Exception as exc:
                        logging.warning(f"Failed to get GStreamer transmission stats: {exc}")
        elif self.use_async_workers:
            # WorkerManager statistics
            if self.worker_manager:
                try:
                    stats["worker_stats"] = self.worker_manager.get_worker_statistics()
                    stats["camera_assignments"] = self.worker_manager.get_camera_assignments()
                except Exception as exc:
                    logging.warning(f"Failed to get worker manager stats: {exc}")
        else:
            # CameraStreamer statistics
            if self.camera_streamer:
                try:
                    stats["transmission_stats"] = self.camera_streamer.get_transmission_stats()
                except Exception as exc:
                    logging.warning(f"Failed to get transmission stats: {exc}")

        # Add camera manager statistics
        if self.camera_manager:
            try:
                stats["camera_manager_stats"] = self.camera_manager.get_statistics()
            except Exception as exc:
                logging.warning(f"Failed to get camera manager stats: {exc}")

        # Add event listener statistics
        if self.event_listener:
            try:
                stats["event_listener_stats"] = self.event_listener.get_statistics()
            except Exception as exc:
                logging.warning(f"Failed to get event listener stats: {exc}")

        return stats

    def get_config(self) -> Dict:
        """Get current configuration."""
        inputs_config_dict = []
        for config in self.inputs_config:
            inputs_config_dict.append({
                'source': config.source,
                'fps': config.fps,
                'quality': config.quality,
                'width': config.width,
                'height': config.height,
                'camera_id': config.camera_id,
                'camera_key': config.camera_key,
                'camera_group_key': config.camera_group_key,
                'camera_location': config.camera_location,
                'simulate_video_file_stream': config.simulate_video_file_stream,
            })

        return {
            "streaming_gateway_id": self.streaming_gateway_id,
            "inputs_config": inputs_config_dict,
            "force_restart": self.force_restart,
            "use_async_workers": self.use_async_workers,
            "num_workers": self.num_workers,
            "max_cameras_per_worker": self.max_cameras_per_worker,
            "use_gstreamer": self.use_gstreamer,
            "gstreamer_encoder": self.gstreamer_encoder,
            "gstreamer_codec": self.gstreamer_codec,
            "gstreamer_preset": self.gstreamer_preset,
            "gstreamer_gpu_id": self.gstreamer_gpu_id,
            "gstreamer_platform": self.gstreamer_platform,
            "gstreamer_use_hardware_decode": self.gstreamer_use_hardware_decode,
            "gstreamer_use_hardware_jpeg": self.gstreamer_use_hardware_jpeg,
            "gstreamer_jetson_use_nvmm": self.gstreamer_jetson_use_nvmm,
            "gstreamer_frame_optimizer_mode": self.gstreamer_frame_optimizer_mode,
            "gstreamer_fallback_on_error": self.gstreamer_fallback_on_error,
            "gstreamer_verbose_logging": self.gstreamer_verbose_logging,
        }

    def _emergency_cleanup(self):
        """Emergency cleanup handler for unexpected shutdowns."""
        try:
            # Only run if streaming is still active
            if self.is_streaming:
                logging.warning("Emergency cleanup triggered - attempting to update gateway status")
                try:
                    self.gateway_util.update_status("stopped")
                    logging.info("Emergency status update successful")
                except Exception as exc:
                    logging.error(f"Emergency status update failed: {exc}")
        except Exception as exc:
            # Catch any errors to prevent atexit handler from failing
            logging.error(f"Error in emergency cleanup: {exc}")

    def __del__(self):
        """Destructor - ensure cleanup on garbage collection."""
        try:
            if hasattr(self, 'is_streaming') and self.is_streaming:
                logging.warning("StreamingGateway being destroyed while still streaming")
                self.stop_streaming()
        except Exception as exc:
            logging.error(f"Error in destructor: {exc}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_streaming()
        # Unregister atexit handler since we're doing controlled cleanup
        if self._cleanup_registered:
            try:
                atexit.unregister(self._emergency_cleanup)
                self._cleanup_registered = False
            except Exception:
                pass
