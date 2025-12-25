"""Debug streaming gateway for testing without Redis/Kafka/API."""
import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .debug_stream_backend import DebugStreamBackend
from .debug_utils import MockSession, create_debug_input_streams, create_camera_configs_from_streams
from ..camera_streamer.camera_streamer import CameraStreamer
from ..camera_streamer.worker_manager import WorkerManager

class DebugStreamingGateway:
    """Debug version of StreamingGateway that works without external dependencies.
    
    This class allows you to test the complete streaming pipeline using local video files
    without requiring:
    - Kafka or Redis servers
    - API authentication
    - Network connectivity
    - Real streaming gateway configuration
    
    Perfect for:
    - Local development and testing
    - CI/CD pipelines
    - Debugging encoding/processing issues
    - Performance testing
    
    Example usage:
        # Simple usage with video files
        gateway = DebugStreamingGateway(
            video_paths=["video1.mp4", "video2.mp4"],
            fps=10,
            loop_videos=True
        )
        gateway.start_streaming()
        
        # Wait and check stats
        time.sleep(30)
        print(gateway.get_statistics())
        
        # Stop
        gateway.stop_streaming()
    """
    
    def __init__(
        self,
        video_paths: List[str],
        fps: int = 10,
        video_codec: str = "h264",
        h265_quality: int = 23,
        use_hardware: bool = False,
        loop_videos: bool = True,
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        log_messages: bool = True,
        save_frame_data: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
        # Worker mode parameters (Mode 2)
        use_workers: bool = False,
        num_workers: Optional[int] = None,
        cpu_percentage: float = 0.8,
        max_cameras_per_worker: int = 10,
    ):
        """Initialize debug streaming gateway.

        Args:
            video_paths: List of video file paths to stream
            fps: Frames per second to stream
            video_codec: Video codec (h264, h265-frame, h265-chunk)
            h265_quality: H.265 quality (0-51, lower=better)
            use_hardware: Use hardware encoding
            loop_videos: Loop videos continuously
            output_dir: Directory to save debug output
            save_to_files: Save streamed messages to files
            log_messages: Log message metadata
            save_frame_data: Include frame data in saved files
            width: Override video width
            height: Override video height
            use_workers: Use multi-process WorkerManager (Mode 2) instead of single-threaded CameraStreamer
            num_workers: Number of worker processes (auto-calculated if None)
            cpu_percentage: Percentage of CPU cores to use for auto-calculation
            max_cameras_per_worker: Maximum cameras per worker process
        """
        # Validate video paths
        for video_path in video_paths:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

        self.video_paths = video_paths
        self.fps = fps
        self.video_codec = video_codec
        self.loop_videos = loop_videos
        self.use_workers = use_workers

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

        # Determine h265_mode from video_codec
        # h265_mode can be "frame" or "stream" (chunk is part of stream mode)
        h265_mode = "frame"
        if "chunk" in video_codec.lower() or "stream" in video_codec.lower():
            h265_mode = "stream"

        # Initialize camera streamer or worker manager based on mode
        self.camera_streamer = None
        self.worker_manager = None

        if use_workers:
            # Mode 2: WorkerManager (multi-process async workers)
            # Create camera configs from input streams
            camera_configs = create_camera_configs_from_streams(self.input_streams)

            # Create stream config for workers
            stream_config = {
                'service_id': 'debug_streaming_gateway',
                'server_type': 'debug',
                'video_codec': video_codec,
                'h265_quality': h265_quality,
                'use_hardware': use_hardware,
                'h265_mode': h265_mode,
                # Debug backend will be injected into workers
                'debug_mode': True,
                'debug_backend_config': {
                    'output_dir': output_dir,
                    'save_to_files': save_to_files,
                    'log_messages': log_messages,
                    'save_frame_data': save_frame_data,
                },
            }

            self.worker_manager = WorkerManager(
                camera_configs=camera_configs,
                stream_config=stream_config,
                num_workers=num_workers,
                cpu_percentage=cpu_percentage,
                max_cameras_per_worker=max_cameras_per_worker,
            )

            self.logger = logging.getLogger(__name__)
            self.logger.info(
                f"DebugStreamingGateway initialized (Worker Mode): "
                f"{len(video_paths)} videos, "
                f"{fps} fps, "
                f"codec={video_codec}, "
                f"workers={self.worker_manager.num_workers}"
            )
        else:
            # Mode 1: CameraStreamer (single-threaded)
            self.camera_streamer = CameraStreamer(
                session=self.session,
                service_id="debug_streaming_gateway",
                server_type="debug",
                video_codec=video_codec,
                h265_quality=h265_quality,
                use_hardware=use_hardware,
                h265_mode=h265_mode,
                gateway_util=None,  # No gateway_util in debug mode
            )

            # Replace MatriceStream with debug backend
            self.camera_streamer.matrice_stream = self.stream_backend

            self.logger = logging.getLogger(__name__)
            self.logger.info(
                f"DebugStreamingGateway initialized (Single-threaded Mode): "
                f"{len(video_paths)} videos, "
                f"{fps} fps, "
                f"codec={video_codec}"
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

        self.logger.info(f"Starting debug streaming with {len(self.input_streams)} videos")

        try:
            if self.use_workers:
                # Mode 2: Worker manager mode
                self.worker_manager.start()
                self.is_streaming = True
                self.start_time = time.time()
                self.logger.info(f"Worker manager started with {self.worker_manager.num_workers} workers")
            else:
                # Mode 1: Single-threaded camera streamer mode
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
                self.logger.info("Debug streaming started successfully")

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
            self.logger.error(f"Failed to start debug streaming: {e}", exc_info=True)
            self.stop_streaming()
            return False
    
    def stop_streaming(self):
        """Stop all streaming."""
        if not self.is_streaming:
            self.logger.warning("Not streaming")
            return

        self.logger.info("Stopping debug streaming")

        try:
            if self.use_workers:
                # Mode 2: Stop worker manager
                self.worker_manager.stop()
            else:
                # Mode 1: Stop camera streamer
                self.camera_streamer.stop_streaming()
                self.stream_backend.close()

            self.is_streaming = False

            runtime = time.time() - self.start_time if self.start_time else 0
            self.logger.info(f"Debug streaming stopped (runtime: {runtime:.1f}s)")

        except Exception as e:
            self.logger.error(f"Error stopping debug streaming: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics.

        Returns:
            Dictionary with streaming statistics
        """
        stats = {
            "is_streaming": self.is_streaming,
            "video_count": len(self.video_paths),
            "fps": self.fps,
            "video_codec": self.video_codec,
            "mode": "worker" if self.use_workers else "single-threaded",
        }

        if self.start_time:
            stats["runtime_seconds"] = time.time() - self.start_time

        if self.use_workers:
            # Mode 2: Get worker manager stats
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
                        # Workers use frames_encoded for frame count
                        total_frames += metrics.get('frames_encoded', 0)
                        total_bytes += metrics.get('bytes_sent', 0)
                        active_streams += report.get('active_cameras', 0)
                        total_errors += metrics.get('encoding_errors', 0)

                stats["transmission_stats"] = {
                    "total_frames_sent": total_frames,
                    "total_bytes_sent": total_bytes,
                    "active_streams": active_streams,
                    "num_workers": worker_stats.get('num_workers', self.worker_manager.num_workers),
                    "running_workers": worker_stats.get('running_workers', 0),
                    "total_errors": total_errors,
                }

                # Calculate derived metrics
                if self.start_time:
                    duration = time.time() - self.start_time
                    stats["avg_fps"] = total_frames / duration if duration > 0 else 0
                    stats["bandwidth_mbps"] = (total_bytes * 8) / (duration * 1_000_000) if duration > 0 else 0

            except Exception as e:
                self.logger.warning(f"Failed to get worker stats: {e}")
                stats["transmission_stats"] = {}
        else:
            # Mode 1: Get camera streamer stats
            try:
                transmission_stats = self.camera_streamer.get_transmission_stats()

                # Normalize field names for consistency
                # CameraStreamer uses frames_sent_full, total_frames_processed
                total_frames = transmission_stats.get("total_frames_processed", 0)
                total_bytes = transmission_stats.get("total_bytes_sent", 0)

                # Get backend stats for additional metrics
                backend_stats = self.stream_backend.get_statistics()
                if not total_frames and backend_stats:
                    total_frames = backend_stats.get("total_messages", 0)

                # Update transmission_stats with normalized field names
                transmission_stats["total_frames_sent"] = total_frames
                stats["transmission_stats"] = transmission_stats

                # Calculate derived metrics
                if self.start_time:
                    duration = time.time() - self.start_time
                    stats["avg_fps"] = total_frames / duration if duration > 0 else 0
                    stats["bandwidth_mbps"] = (total_bytes * 8) / (duration * 1_000_000) if duration > 0 else 0

            except Exception as e:
                self.logger.warning(f"Failed to get transmission stats: {e}")

            # Get backend stats
            try:
                stats["backend_stats"] = self.stream_backend.get_statistics()
            except Exception as e:
                self.logger.warning(f"Failed to get backend stats: {e}")

        return stats
    
    def get_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get timing statistics.

        Args:
            stream_key: Specific stream or None for all

        Returns:
            Timing statistics
        """
        if self.use_workers:
            # Worker mode doesn't support per-stream timing stats directly
            return {"mode": "worker", "note": "Per-stream timing not available in worker mode"}
        return self.camera_streamer.get_stream_timing_stats(stream_key)

    def reset_stats(self):
        """Reset all statistics."""
        if self.use_workers:
            # Worker mode - no direct reset capability
            self.logger.info("Statistics reset (worker mode - limited reset)")
        else:
            self.camera_streamer.reset_transmission_stats()
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
            f"DebugStreamingGateway("
            f"videos={len(self.video_paths)}, "
            f"fps={self.fps}, "
            f"mode={mode_str}, "
            f"streaming={self.is_streaming})"
        )


class DebugStreamingAction:
    """Debug version of StreamingAction for testing without API.
    
    This is a simplified version that doesn't require action IDs, API calls,
    or health monitoring. Perfect for local testing.
    
    Example usage:
        action = DebugStreamingAction(
            video_paths=["video1.mp4", "video2.mp4"],
            fps=10
        )
        action.start()
        time.sleep(30)
        action.stop()
    """
    
    def __init__(
        self,
        video_paths: List[str],
        fps: int = 10,
        video_codec: str = "h265-frame",
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        **kwargs
    ):
        """Initialize debug streaming action.
        
        Args:
            video_paths: List of video file paths
            fps: Frames per second
            video_codec: Video codec
            output_dir: Output directory for debug files
            save_to_files: Save messages to files
            **kwargs: Additional arguments for DebugStreamingGateway
        """
        self.gateway = DebugStreamingGateway(
            video_paths=video_paths,
            fps=fps,
            video_codec=video_codec,
            output_dir=output_dir,
            save_to_files=save_to_files,
            **kwargs
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DebugStreamingAction initialized with {len(video_paths)} videos")
    
    def start(self, block: bool = False) -> bool:
        """Start streaming action.
        
        Args:
            block: Block until manually stopped
            
        Returns:
            True if started successfully
        """
        self.logger.info("Starting debug streaming action")
        return self.gateway.start_streaming(block=block)
    
    def stop(self):
        """Stop streaming action."""
        self.logger.info("Stopping debug streaming action")
        self.gateway.stop_streaming()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status.
        
        Returns:
            Status dictionary
        """
        return self.gateway.get_statistics()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.logger.error(f"Exception in context: {exc_val}", exc_info=True)
        self.stop()

