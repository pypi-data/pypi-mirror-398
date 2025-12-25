"""Debug GStreamer gateway for testing without Redis/Kafka/API."""
import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .debug_stream_backend import DebugStreamBackend
from .debug_utils import MockSession, create_debug_input_streams, create_camera_configs_from_streams

# Check GStreamer availability
GSTREAMER_AVAILABLE = False
GSTREAMER_WORKER_AVAILABLE = False
try:
    from ..camera_streamer.gstreamer_camera_streamer import (
        GStreamerCameraStreamer,
        GStreamerConfig,
        is_gstreamer_available,
    )
    GSTREAMER_AVAILABLE = is_gstreamer_available()

    # Try to import GStreamerWorkerManager
    from ..camera_streamer.gstreamer_worker_manager import GStreamerWorkerManager
    GSTREAMER_WORKER_AVAILABLE = True
except ImportError:
    pass


class DebugGStreamerGateway:
    """Debug version of GStreamer streaming gateway for local testing.

    This class allows you to test the complete GStreamer pipeline using:
    - Local video files (MP4, AVI, etc.)
    - RTSP streams
    - USB cameras
    - Test patterns

    Without requiring:
    - Kafka or Redis servers
    - API authentication
    - Network connectivity
    - Real streaming gateway configuration

    Perfect for:
    - Local development and testing
    - CI/CD pipelines
    - GStreamer encoder testing (NVENC, x264, OpenH264, JPEG)
    - Performance benchmarking
    - Frame optimization testing

    Example usage:
        # JPEG frame-by-frame with NVENC fallback
        gateway = DebugGStreamerGateway(
            video_paths=["video1.mp4", "video2.mp4"],
            fps=30,
            gstreamer_encoder="jpeg",
            jpeg_quality=85,
            loop_videos=True
        )
        gateway.start_streaming()

        # Wait and check stats
        time.sleep(30)
        stats = gateway.get_statistics()
        print(f"FPS: {stats['avg_fps']:.1f}")
        print(f"Bandwidth: {stats['bandwidth_mbps']:.2f} Mbps")
        print(f"Cache hits: {stats['cache_efficiency']:.1f}%")

        # Stop
        gateway.stop_streaming()

        # Test NVENC hardware encoding
        gateway = DebugGStreamerGateway(
            video_paths=["high_res_video.mp4"],
            fps=60,
            gstreamer_encoder="nvenc",
            gstreamer_codec="h264",
            gstreamer_preset="low-latency",
            gstreamer_gpu_id=0
        )
        gateway.start_streaming()
    """

    def __init__(
        self,
        video_paths: List[str],
        fps: int = 30,
        loop_videos: bool = True,
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        log_messages: bool = True,
        save_frame_data: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        # GStreamer specific options
        gstreamer_encoder: str = "jpeg",  # jpeg, nvenc, x264, openh264, auto
        gstreamer_codec: str = "h264",  # h264, h265
        gstreamer_preset: str = "low-latency",  # NVENC preset
        gstreamer_gpu_id: int = 0,  # GPU device ID
        jpeg_quality: int = 85,  # JPEG quality (1-100)
        # Frame optimization
        enable_frame_optimizer: bool = True,
        frame_optimizer_scale: float = 0.4,
        frame_optimizer_threshold: float = 0.05,
        # Worker mode parameters (Mode 4)
        use_workers: bool = False,
        num_workers: Optional[int] = None,
        cpu_percentage: float = 0.8,
        max_cameras_per_worker: int = 10,
    ):
        """Initialize debug GStreamer gateway.

        Args:
            video_paths: List of video file paths to stream
            fps: Frames per second to stream
            loop_videos: Loop videos continuously
            output_dir: Directory to save debug output
            save_to_files: Save streamed messages to files
            log_messages: Log message metadata
            save_frame_data: Include frame data in saved files
            width: Override video width
            height: Override video height
            gstreamer_encoder: GStreamer encoder (jpeg, nvenc, x264, openh264, auto)
            gstreamer_codec: Codec for hardware/software encoders (h264, h265)
            gstreamer_preset: NVENC preset (low-latency, high-quality, lossless)
            gstreamer_gpu_id: GPU device ID for NVENC
            jpeg_quality: JPEG quality 1-100 (higher=better, larger)
            enable_frame_optimizer: Enable frame similarity detection
            frame_optimizer_scale: Downscale factor for similarity detection
            frame_optimizer_threshold: Similarity threshold (lower=stricter)
            use_workers: Use multi-process GStreamerWorkerManager (Mode 4) instead of single-threaded
            num_workers: Number of worker processes (auto-calculated if None)
            cpu_percentage: Percentage of CPU cores to use for auto-calculation
            max_cameras_per_worker: Maximum cameras per worker process
        """
        # Check GStreamer availability
        if not GSTREAMER_AVAILABLE:
            raise RuntimeError(
                "GStreamer not available. Install with:\n"
                "  pip install PyGObject\n"
                "  apt-get install gstreamer1.0-tools gstreamer1.0-plugins-*"
            )

        # Check worker mode availability
        if use_workers and not GSTREAMER_WORKER_AVAILABLE:
            raise RuntimeError(
                "GStreamerWorkerManager not available. Worker mode requires the full package."
            )

        # Validate video paths
        for video_path in video_paths:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

        self.video_paths = video_paths
        self.fps = fps
        self.loop_videos = loop_videos
        self.use_workers = use_workers
        self.enable_frame_optimizer = enable_frame_optimizer

        # Create mock session
        self.session = MockSession()

        # Create debug stream backend (replaces Kafka/Redis)
        self.stream_backend = DebugStreamBackend(
            output_dir=output_dir,
            save_to_files=save_to_files,
            log_messages=log_messages,
            save_frame_data=save_frame_data
        )

        # Create input streams from video paths
        self.input_streams = create_debug_input_streams(
            video_paths=video_paths,
            fps=fps,
            loop=loop_videos
        )

        # Override dimensions if provided
        if width or height:
            for stream in self.input_streams:
                if width:
                    stream.width = width
                if height:
                    stream.height = height

        # Create GStreamer config
        self.gstreamer_config = GStreamerConfig(
            encoder=gstreamer_encoder,
            codec=gstreamer_codec,
            preset=gstreamer_preset,
            gpu_id=gstreamer_gpu_id,
            jpeg_quality=jpeg_quality,
        )

        # Frame optimizer config
        self.frame_optimizer_config = {
            "scale": frame_optimizer_scale,
            "similarity_threshold": frame_optimizer_threshold,
            "diff_threshold": 15,
            "bg_update_interval": 10,
        }

        # Initialize camera streamer or worker manager based on mode
        self.camera_streamer = None
        self.worker_manager = None

        if use_workers:
            # Mode 4: GStreamerWorkerManager (multi-process GStreamer workers)
            # Create camera configs from input streams
            camera_configs = create_camera_configs_from_streams(self.input_streams)

            # Create stream config for workers
            stream_config = {
                'service_id': 'debug_gstreamer_gateway',
                'server_type': 'debug',
                'gstreamer_encoder': gstreamer_encoder,
                'gstreamer_codec': gstreamer_codec,
                'gstreamer_preset': gstreamer_preset,
                'gstreamer_gpu_id': gstreamer_gpu_id,
                'jpeg_quality': jpeg_quality,
                'frame_optimizer_enabled': enable_frame_optimizer,
                'frame_optimizer_config': self.frame_optimizer_config,
                # Debug backend will be injected into workers
                'debug_mode': True,
                'debug_backend_config': {
                    'output_dir': output_dir,
                    'save_to_files': save_to_files,
                    'log_messages': log_messages,
                    'save_frame_data': save_frame_data,
                },
            }

            self.worker_manager = GStreamerWorkerManager(
                camera_configs=camera_configs,
                stream_config=stream_config,
                num_workers=num_workers,
                cpu_percentage=cpu_percentage,
                max_cameras_per_worker=max_cameras_per_worker,
                gstreamer_encoder=gstreamer_encoder,
                gstreamer_codec=gstreamer_codec,
                gstreamer_preset=gstreamer_preset,
                gpu_id=gstreamer_gpu_id,
            )

            self.logger = logging.getLogger(__name__)
            self.logger.info(
                f"DebugGStreamerGateway initialized (Worker Mode): "
                f"{len(video_paths)} videos, "
                f"{fps} fps, "
                f"encoder={gstreamer_encoder}, "
                f"codec={gstreamer_codec}, "
                f"workers={self.worker_manager.num_workers}"
            )
        else:
            # Mode 3: GStreamerCameraStreamer (single-threaded)
            self.camera_streamer = GStreamerCameraStreamer(
                session=self.session,
                service_id="debug_gstreamer_gateway",
                server_type="debug",
                gstreamer_config=self.gstreamer_config,
                frame_optimizer_enabled=enable_frame_optimizer,
                frame_optimizer_config=self.frame_optimizer_config,
                gateway_util=None,  # No gateway_util in debug mode
            )

            # Replace MatriceStream with debug backend
            self.camera_streamer.matrice_stream = self.stream_backend

            self.logger = logging.getLogger(__name__)
            self.logger.info(
                f"DebugGStreamerGateway initialized (Single-threaded Mode): "
                f"{len(video_paths)} videos, "
                f"{fps} fps, "
                f"encoder={gstreamer_encoder}, "
                f"codec={gstreamer_codec}"
            )

        # State
        self.is_streaming = False
        self.start_time = None

    def start_streaming(self, block: bool = False) -> bool:
        """Start streaming all video files.

        Args:
            block: If True, block until manually stopped

        Returns:
            True if started successfully
        """
        if self.is_streaming:
            self.logger.warning("Already streaming")
            return False

        self.logger.info(f"Starting GStreamer debug streaming with {len(self.input_streams)} videos")

        try:
            if self.use_workers:
                # Mode 4: Worker manager mode
                self.worker_manager.start()
                self.is_streaming = True
                self.start_time = time.time()
                self.logger.info(f"GStreamer worker manager started with {self.worker_manager.num_workers} workers")
            else:
                # Mode 3: Single-threaded camera streamer mode
                # Register topics and start streams
                for i, input_stream in enumerate(self.input_streams):
                    stream_key = input_stream.camera_key
                    topic = input_stream.camera_input_topic

                    # Register topic
                    self.camera_streamer.register_stream_topic(stream_key, topic)
                    self.stream_backend.setup(topic)

                    # Start streaming
                    success = self.camera_streamer.start_background_stream(
                        input=input_stream.source,
                        fps=input_stream.fps,
                        stream_key=stream_key,
                        stream_group_key=input_stream.camera_group_key,
                        quality=input_stream.quality,
                        width=input_stream.width,
                        height=input_stream.height,
                        simulate_video_file_stream=input_stream.simulate_video_file_stream,
                        camera_location=input_stream.camera_location,
                    )

                    if not success:
                        self.logger.error(f"Failed to start stream {i}: {input_stream.source}")
                        self.stop_streaming()
                        return False

                    self.logger.info(f"Started stream {i}: {input_stream.source}")

                self.is_streaming = True
                self.start_time = time.time()
                self.logger.info("GStreamer debug streaming started successfully")

            if block:
                self.logger.info("Blocking mode - press Ctrl+C to stop")
                try:
                    while self.is_streaming:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("Interrupted by user")
                    self.stop_streaming()

            return True

        except Exception as e:
            self.logger.error(f"Failed to start GStreamer debug streaming: {e}", exc_info=True)
            self.stop_streaming()
            return False

    def stop_streaming(self):
        """Stop all streaming."""
        if not self.is_streaming:
            self.logger.warning("Not streaming")
            return

        self.logger.info("Stopping GStreamer debug streaming")

        try:
            if self.use_workers:
                # Mode 4: Stop worker manager
                self.worker_manager.stop()
            else:
                # Mode 3: Stop camera streamer
                self.camera_streamer.stop_streaming()
                self.stream_backend.close()

            self.is_streaming = False

            runtime = time.time() - self.start_time if self.start_time else 0
            self.logger.info(f"GStreamer debug streaming stopped (runtime: {runtime:.1f}s)")

        except Exception as e:
            self.logger.error(f"Error stopping GStreamer debug streaming: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive streaming statistics.

        Returns:
            Dictionary with streaming statistics including:
            - Basic info (video count, fps, encoder, codec)
            - Runtime metrics (duration, uptime)
            - Transmission stats (frames sent, bytes, topics)
            - Performance metrics (avg fps, bandwidth)
            - Frame optimization metrics (cache efficiency, similarity rate)
            - GStreamer pipeline metrics (per-stream stats)
        """
        stats = {
            "is_streaming": self.is_streaming,
            "video_count": len(self.video_paths),
            "fps": self.fps,
            "encoder": self.gstreamer_config.encoder,
            "codec": self.gstreamer_config.codec,
            "jpeg_quality": self.gstreamer_config.jpeg_quality,
            "mode": "worker" if self.use_workers else "single-threaded",
            "frame_optimizer_enabled": self.enable_frame_optimizer,
        }

        if self.start_time:
            stats["runtime_seconds"] = time.time() - self.start_time

        if self.use_workers:
            # Mode 4: Get worker manager stats
            try:
                # Get worker statistics
                worker_stats = self.worker_manager.get_worker_statistics()
                stats["worker_stats"] = worker_stats

                # Calculate aggregate transmission stats from health_reports
                total_frames = 0
                total_bytes = 0
                active_streams = 0
                total_errors = 0

                # The worker_stats has a 'health_reports' dict with per-worker metrics
                health_reports = worker_stats.get('health_reports', {})
                for worker_id, report in health_reports.items():
                    if isinstance(report, dict):
                        metrics = report.get('metrics', {})
                        total_frames += metrics.get('frames_encoded', 0)
                        # Note: bytes aren't tracked directly, estimate from frames
                        active_streams += report.get('active_cameras', 0)
                        total_errors += metrics.get('encoding_errors', 0)

                # Estimate bytes (we don't have direct tracking in gstreamer_worker)
                # Using rough estimate of 30KB per JPEG frame at 640x480
                estimated_bytes = total_frames * 30000

                stats["transmission_stats"] = {
                    "total_frames_sent": total_frames,
                    "total_bytes_sent": estimated_bytes,
                    "active_streams": active_streams,
                    "num_workers": worker_stats.get('num_workers', self.worker_manager.num_workers),
                    "running_workers": worker_stats.get('running_workers', 0),
                    "total_errors": total_errors,
                }

                # Calculate derived metrics
                if self.start_time:
                    duration = time.time() - self.start_time
                    stats["avg_fps"] = total_frames / duration if duration > 0 else 0
                    stats["bandwidth_mbps"] = (estimated_bytes * 8) / (duration * 1_000_000) if duration > 0 else 0

            except Exception as e:
                self.logger.warning(f"Failed to get worker stats: {e}")
                stats["transmission_stats"] = {}
        else:
            # Mode 3: Get camera streamer stats
            try:
                transmission_stats = self.camera_streamer.get_transmission_stats()

                # Normalize field names for consistency
                # GStreamerCameraStreamer uses total_frames_processed
                total_frames = transmission_stats.get("total_frames_processed", 0)
                total_bytes = transmission_stats.get("total_bytes_sent", 0)

                # Get GStreamer-specific stats
                gstreamer_stats = transmission_stats.get("gstreamer", {})
                if not total_bytes and gstreamer_stats:
                    total_bytes = gstreamer_stats.get("total_bytes", 0)

                # Get backend stats for additional metrics
                backend_stats = self.stream_backend.get_statistics()
                if not total_frames and backend_stats:
                    total_frames = backend_stats.get("total_messages", 0)

                # Update transmission_stats with normalized field names
                transmission_stats["total_frames_sent"] = total_frames
                transmission_stats["total_bytes_sent"] = total_bytes
                stats["transmission_stats"] = transmission_stats

                # Calculate derived metrics
                if self.start_time:
                    duration = time.time() - self.start_time
                    stats["avg_fps"] = total_frames / duration if duration > 0 else 0
                    stats["bandwidth_mbps"] = (total_bytes * 8) / (duration * 1_000_000) if duration > 0 else 0

            except Exception as e:
                self.logger.warning(f"Failed to get transmission stats: {e}")

            # Get frame optimizer metrics (only available in single-threaded mode)
            try:
                if self.camera_streamer.frame_optimizer.enabled:
                    opt_metrics = self.camera_streamer.frame_optimizer.get_metrics()
                    stats["frame_optimizer_metrics"] = opt_metrics

                    # Calculate cache efficiency
                    total_checks = opt_metrics.get("total_checks", 0)
                    similar_count = opt_metrics.get("similar_count", 0)
                    stats["cache_efficiency"] = (similar_count / total_checks * 100) if total_checks > 0 else 0

            except Exception as e:
                self.logger.warning(f"Failed to get frame optimizer metrics: {e}")

            # Get backend stats
            try:
                stats["backend_stats"] = self.stream_backend.get_statistics()
            except Exception as e:
                self.logger.warning(f"Failed to get backend stats: {e}")

            # Get per-stream timing stats
            try:
                timing_stats = {}
                for input_stream in self.input_streams:
                    stream_key = input_stream.camera_key
                    timing = self.camera_streamer.get_stream_timing_stats(stream_key)
                    if timing:
                        timing_stats[stream_key] = timing
                stats["timing_stats"] = timing_stats
            except Exception as e:
                self.logger.warning(f"Failed to get timing stats: {e}")

        return stats

    def get_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed timing statistics.

        Args:
            stream_key: Specific stream or None for all

        Returns:
            Timing statistics with read_time, write_time, process_time breakdown
        """
        if self.use_workers:
            # Worker mode doesn't support per-stream timing stats directly
            return {"mode": "worker", "note": "Per-stream timing not available in worker mode"}
        return self.camera_streamer.get_stream_timing_stats(stream_key)

    def produce_request(self, input_data: bytes, topic: str, key: Optional[str] = None) -> bool:
        """Synchronous message production for testing.

        Args:
            input_data: Message data
            topic: Topic/stream name
            key: Message key

        Returns:
            True if successful
        """
        return self.camera_streamer.produce_request(input_data, topic, key)

    async def async_produce_request(self, input_data: bytes, topic: str, key: Optional[str] = None) -> bool:
        """Async message production for testing.

        Args:
            input_data: Message data
            topic: Topic/stream name
            key: Message key

        Returns:
            True if successful
        """
        return await self.camera_streamer.async_produce_request(input_data, topic, key)

    def refresh_connection_info(self) -> bool:
        """Refresh connection (no-op for debug mode).

        Returns:
            True (always successful in debug mode)
        """
        self.logger.info("refresh_connection_info called (no-op in debug mode)")
        return True

    def reset_stats(self):
        """Reset all statistics."""
        if self.use_workers:
            # Worker mode - no direct reset capability
            self.logger.info("Statistics reset (worker mode - limited reset)")
        else:
            self.camera_streamer.reset_transmission_stats()
            if self.camera_streamer.frame_optimizer.enabled:
                self.camera_streamer.frame_optimizer.reset_metrics()
            self.logger.info("Statistics reset")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.logger.error(f"Exception in context: {exc_val}", exc_info=True)
        self.stop_streaming()

    def __repr__(self):
        """String representation."""
        mode_str = f"workers={self.worker_manager.num_workers}" if self.use_workers else "single-threaded"
        return (
            f"DebugGStreamerGateway("
            f"videos={len(self.video_paths)}, "
            f"fps={self.fps}, "
            f"encoder={self.gstreamer_config.encoder}, "
            f"mode={mode_str}, "
            f"streaming={self.is_streaming})"
        )
