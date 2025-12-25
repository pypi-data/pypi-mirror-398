"""Async camera worker process for handling multiple cameras concurrently.

This module implements an async event loop worker that handles multiple cameras
in a single process using asyncio for efficient I/O-bound operations.
"""
import asyncio
import logging
import time
import multiprocessing
import os
import psutil
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Union
from collections import deque
import cv2
from pathlib import Path

from matrice_common.optimize import FrameOptimizer

from .video_capture_manager import VideoCaptureManager
from .frame_processor import FrameProcessor
from .message_builder import StreamMessageBuilder
from .stream_statistics import StreamStatistics

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["KMP_NUM_THREADS"] = "1"
os.environ["KMP_BLOCKTIME"] = "0"
os.environ["TBB_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import cv2
cv2.setNumThreads(1)
cv2.setUseOptimized(True)
cv2.ocl.setUseOpenCL(False)


class AsyncCameraWorker:
    """Async worker process that handles multiple cameras concurrently.

    This worker runs an async event loop to handle I/O-bound operations
    (video capture, Redis writes) for multiple cameras efficiently.
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
        frame_optimizer_enabled: bool = True,
        frame_optimizer_config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize async camera worker.

        Args:
            worker_id: Unique identifier for this worker
            camera_configs: List of camera configurations to handle
            stream_config: Streaming configuration (Redis, Kafka, etc.)
            stop_event: Event to signal worker shutdown
            health_queue: Queue for reporting health status
            command_queue: Queue for receiving dynamic camera commands (add/remove/update)
            response_queue: Queue for sending command responses back to manager
        """
        self.worker_id = worker_id
        self.camera_configs = camera_configs
        self.stream_config = stream_config
        self.stop_event = stop_event
        self.health_queue = health_queue
        self.command_queue = command_queue
        self.response_queue = response_queue

        # Setup logging with worker ID
        self.logger = logging.getLogger(f"AsyncWorker-{worker_id}")
        self.logger.info(f"Initializing worker {worker_id} with {len(camera_configs)} cameras")

        # Initialize components
        self.capture_manager = VideoCaptureManager()
        self.message_builder = StreamMessageBuilder(
            service_id=stream_config.get('service_id', 'streaming_gateway'),
            strip_input_content=False
        )
        self.statistics = StreamStatistics()

        # Track camera tasks
        self.camera_tasks: Dict[str, asyncio.Task] = {}
        self.captures: Dict[str, cv2.VideoCapture] = {}

        # Setup async Redis client
        self.redis_client = None

        # Initialize frame optimizer for skipping similar frames
        frame_optimizer_config = frame_optimizer_config or {}
        self.frame_optimizer = FrameOptimizer(
            enabled=frame_optimizer_enabled,
            scale=frame_optimizer_config.get("scale", 0.4),
            diff_threshold=frame_optimizer_config.get("diff_threshold", 15),
            similarity_threshold=frame_optimizer_config.get("similarity_threshold", 0.05),
            bg_update_interval=frame_optimizer_config.get("bg_update_interval", 10),
        )
        self._last_sent_frame_ids: Dict[str, str] = {}  # stream_key -> last sent frame_id

        # ThreadPoolExecutor for I/O-bound frame capture only
        # Encoding is done inline (cv2.imencode releases GIL, ~5ms for 480p)
        #
        # Thread scaling strategy:
        # - Video files are I/O bound (disk read), not CPU bound
        # - More threads = more concurrent reads = less contention
        # - But TOO many threads causes burst frame arrivals → Redis write queue backup
        # - Cap at 64 threads to balance I/O parallelism vs write contention
        num_cameras = len(camera_configs)
        # Use 1 thread per camera, capped at 64 to prevent write burst contention
        num_capture_threads = min(64, max(8, num_cameras))
        self.capture_executor = ThreadPoolExecutor(max_workers=num_capture_threads)
        self.num_capture_threads = num_capture_threads

        # Track encoding metrics (encoding done inline, not in executor)
        self.num_encoding_processes = 0  # Inline encoding, no separate processes

        # ========================================================================
        # Performance Metrics Tracking
        # ========================================================================
        self._encoding_times = deque(maxlen=100)
        self._frame_times = deque(maxlen=100)
        self._frames_encoded = 0
        self._encoding_errors = 0
        self._last_metrics_log = time.time()
        self._metrics_log_interval = 30.0
        self._process_info = psutil.Process(os.getpid())

        self.logger.info(
            f"Worker {worker_id}: Created capture pool ({num_capture_threads} threads), "
            f"encoding inline (no executor - cv2.imencode releases GIL)"
        )
        self._log_system_resources("INIT")

    async def _log_metrics(self) -> None:
        """Log comprehensive worker metrics periodically."""
        try:
            # Per-camera metrics (use StreamStatistics methods)
            for stream_key in self.camera_tasks.keys():
                self.statistics.log_detailed_stats(stream_key)

            # Frame optimizer metrics
            if self.frame_optimizer.enabled:
                opt_metrics = self.frame_optimizer.get_metrics()
                self.logger.info(
                    f"Worker {self.worker_id} Frame Optimizer: "
                    f"similarity_rate={opt_metrics['similarity_rate']:.1f}%, "
                    f"active_streams={opt_metrics['active_streams']}"
                )

            # Worker-level encoding metrics
            if self._encoding_times:
                avg_encoding_ms = (sum(self._encoding_times) / len(self._encoding_times)) * 1000
                self.logger.info(
                    f"Worker {self.worker_id} Encoding Pool: "
                    f"avg_time={avg_encoding_ms:.1f}ms, "
                    f"frames_encoded={self._frames_encoded}, "
                    f"errors={self._encoding_errors}, "
                    f"pool_size={self.num_encoding_processes}"
                )

            # System resources
            proc_cpu = self._process_info.cpu_percent(interval=0.1)
            memory_mb = self._process_info.memory_info().rss / 1024 / 1024

            self.logger.info(
                f"Worker {self.worker_id} Resources: "
                f"CPU={proc_cpu:.1f}%, "
                f"Memory={memory_mb:.1f}MB, "
                f"Active cameras={len(self.camera_tasks)}"
            )

            # Aggregate stats (all streams)
            self.statistics.log_aggregated_stats()

        except Exception as exc:
            self.logger.warning(f"Worker {self.worker_id}: Failed to log metrics: {exc}")

    def _log_system_resources(self, context: str = ""):
        """Simple fallback for initial resource logging.

        Args:
            context: Optional context string
        """
        try:
            proc_cpu = self._process_info.cpu_percent(interval=0.1)
            memory_mb = self._process_info.memory_info().rss / 1024 / 1024
            self.logger.info(
                f"Worker {self.worker_id} [{context}]: "
                f"CPU={proc_cpu:.1f}%, Memory={memory_mb:.1f}MB, "
                f"Encoding pool size={self.num_encoding_processes}"
            )
        except Exception as exc:
            self.logger.warning(f"Worker {self.worker_id}: Failed to log resources: {exc}")


    async def initialize(self):
        """Initialize async resources (Redis client, etc.)."""
        try:
            # Import and initialize async Redis client
            from matrice_common.stream import MatriceStream, StreamType

            # Create MatriceStream with async support
            # Unpack stream_config as keyword arguments (MatriceStream expects **config)
            self.stream = MatriceStream(
                stream_type=StreamType.REDIS,
                **self.stream_config
            )

            # Use async client
            self.redis_client = self.stream.async_client
            await self.redis_client.setup_client()

            self.logger.info(f"Worker {self.worker_id}: Initialized async Redis client")

        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Failed to initialize: {exc}", exc_info=True)
            raise

    async def run(self):
        """Main worker loop - starts async tasks for all cameras and handles commands."""
        try:
            # Initialize async resources
            await self.initialize()

            # Start initial camera tasks using internal method
            for camera_config in self.camera_configs:
                await self._add_camera_internal(camera_config)

            # Report initial health
            self._report_health("running", len(self.camera_tasks))

            # Start command handler task if command queue is provided
            command_task = None
            if self.command_queue:
                command_task = asyncio.create_task(
                    self._command_handler(),
                    name="command-handler"
                )
                self.logger.info(f"Worker {self.worker_id}: Command handler started")

            # Monitor tasks and stop event
            while not self.stop_event.is_set():
                # Check for completed/failed tasks
                for stream_key, task in list(self.camera_tasks.items()):
                    if task.done():
                        try:
                            # Check if task raised exception
                            task.result()
                            self.logger.warning(f"Worker {self.worker_id}: Camera {stream_key} task completed")
                        except Exception as exc:
                            self.logger.error(f"Worker {self.worker_id}: Camera {stream_key} task failed: {exc}")

                        # Remove completed task
                        del self.camera_tasks[stream_key]

                # Report health periodically
                self._report_health("running", len(self.camera_tasks))

                # Sleep briefly
                await asyncio.sleep(1.0)

            # Stop event set - graceful shutdown
            self.logger.info(f"Worker {self.worker_id}: Stop event detected, shutting down...")

            # Cancel command handler if running
            if command_task and not command_task.done():
                command_task.cancel()
                try:
                    await command_task
                except asyncio.CancelledError:
                    pass

            await self._shutdown()

        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Fatal error in run loop: {exc}", exc_info=True)
            self._report_health("error", error=str(exc))
            raise

    async def _camera_handler(self, camera_config: Dict[str, Any]):
        """Handle a single camera with async I/O.

        Features:
        - Infinite retry with exponential backoff for camera reconnection
        - Video file looping via simulate_video_file_stream parameter
        - Two-level loop: outer (reconnection) + inner (frame processing)

        Args:
            camera_config: Camera configuration dictionary
        """
        stream_key = camera_config['stream_key']
        stream_group_key = camera_config.get('stream_group_key', 'default')
        source = camera_config['source']
        topic = camera_config['topic']
        fps = camera_config.get('fps', 30)
        quality = camera_config.get('quality', 90)
        width = camera_config.get('width')
        height = camera_config.get('height')
        camera_location = camera_config.get('camera_location', 'Unknown')
        simulate_video_file_stream = camera_config.get('simulate_video_file_stream', False)

        # Retry settings (similar to RetryManager in old flow)
        MIN_RETRY_COOLDOWN = 5   # 5 second minimum backoff
        MAX_RETRY_COOLDOWN = 30  # 30 second maximum backoff
        retry_cycle = 0
        max_frame_failures = 10  # Max failures within a single connection

        # Track source type for video looping decision
        source_type = None

        # OUTER LOOP: Infinite retry for reconnection (similar to old CameraStreamer)
        while not self.stop_event.is_set():
            cap = None
            consecutive_failures = 0
            frame_counter = 0

            try:
                # Prepare source (download if URL)
                prepared_source = self.capture_manager.prepare_source(source, stream_key)

                # Open capture in thread pool (blocking operation)
                cap, source_type = await asyncio.to_thread(
                    self.capture_manager.open_capture,
                    prepared_source, width, height
                )
                self.captures[stream_key] = cap

                # Get video properties
                video_props = self.capture_manager.get_video_properties(cap)
                original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                actual_width, actual_height = FrameProcessor.calculate_actual_dimensions(
                    original_width, original_height, width, height
                )

                # Reset retry cycle on successful connection
                retry_cycle = 0

                self.logger.info(
                    f"Worker {self.worker_id}: Camera {stream_key} connected - "
                    f"{actual_width}x{actual_height} @ {fps} FPS (type: {source_type})"
                )

                # INNER LOOP: Process frames
                while not self.stop_event.is_set():
                    try:
                        # Read frame (blocking - run in dedicated capture thread pool)
                        read_start = time.time()
                        loop = asyncio.get_event_loop()
                        ret, frame = await loop.run_in_executor(
                            self.capture_executor,  # Dedicated thread pool for I/O
                            cap.read
                        )
                        read_time = time.time() - read_start

                        if not ret:
                            consecutive_failures += 1

                            # Check for video file end
                            if source_type == "video_file":
                                if simulate_video_file_stream:
                                    self.logger.info(
                                        f"Worker {self.worker_id}: Video {stream_key} ended, "
                                        f"restarting (simulate_video_file_stream=True)"
                                    )
                                    await asyncio.sleep(1.0)  # Brief pause before restart
                                    break  # Break inner loop to restart video in outer loop
                                else:
                                    self.logger.info(
                                        f"Worker {self.worker_id}: Video {stream_key} ended (no loop)"
                                    )
                                    return  # Exit handler completely - video finished

                            # For cameras, check failure threshold before reconnect
                            if consecutive_failures >= max_frame_failures:
                                self.logger.warning(
                                    f"Worker {self.worker_id}: Camera {stream_key} - "
                                    f"{max_frame_failures} consecutive failures, reconnecting..."
                                )
                                break  # Break inner loop to reconnect in outer loop

                            await asyncio.sleep(0.1)
                            continue

                        # Reset failure counter on success
                        consecutive_failures = 0
                        frame_counter += 1

                        # Resize if needed
                        if width or height:
                            frame = FrameProcessor.resize_frame(frame, width, height)

                        # Process and send frame
                        await self._process_and_send_frame(
                            frame, stream_key, stream_group_key, topic,
                            source, video_props, fps, quality,
                            actual_width, actual_height, source_type,
                            frame_counter, camera_location, read_time
                        )

                        # Maintain target FPS for ALL sources (video files AND live cameras)
                        # This prevents overwhelming the encoder by reading at native camera rate (30+ FPS)
                        frame_interval = 1.0 / fps
                        frame_elapsed = time.time() - read_start
                        sleep_time = max(0, frame_interval - frame_elapsed)
                        if sleep_time > 0:
                            await asyncio.sleep(sleep_time)

                    except asyncio.CancelledError:
                        self.logger.info(f"Worker {self.worker_id}: Camera {stream_key} task cancelled")
                        return  # Exit completely on cancellation
                    except Exception as exc:
                        self.logger.error(
                            f"Worker {self.worker_id}: Error in camera {stream_key}: {exc}",
                            exc_info=True
                        )
                        consecutive_failures += 1
                        if consecutive_failures >= max_frame_failures:
                            self.logger.warning(
                                f"Worker {self.worker_id}: Camera {stream_key} - "
                                f"max failures in inner loop, reconnecting..."
                            )
                            break  # Break inner loop to reconnect
                        await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                self.logger.info(f"Worker {self.worker_id}: Camera {stream_key} task cancelled during setup")
                return  # Exit completely on cancellation
            except Exception as exc:
                self.logger.error(
                    f"Worker {self.worker_id}: Camera {stream_key} connection error: {exc}",
                    exc_info=True
                )
            finally:
                # Cleanup capture for this iteration
                if cap:
                    try:
                        cap.release()
                    except Exception:
                        pass
                if stream_key in self.captures:
                    del self.captures[stream_key]

            # Determine if we should retry or exit
            if self.stop_event.is_set():
                break  # Exit if stop requested

            # For video files with simulate_video_file_stream, restart immediately (no backoff)
            if source_type == "video_file" and simulate_video_file_stream:
                self.logger.info(f"Worker {self.worker_id}: Restarting video {stream_key}")
                continue  # Restart immediately

            # For cameras, apply exponential backoff before reconnection
            cooldown = min(MAX_RETRY_COOLDOWN, MIN_RETRY_COOLDOWN + retry_cycle)
            self.logger.info(
                f"Worker {self.worker_id}: Retrying camera {stream_key} in {cooldown}s "
                f"(retry cycle {retry_cycle})"
            )
            await asyncio.sleep(cooldown)
            retry_cycle += 1

        self.logger.info(f"Worker {self.worker_id}: Camera handler for {stream_key} exited")

    async def _process_and_send_frame(
        self,
        frame,
        stream_key: str,
        stream_group_key: str,
        topic: str,
        source: Union[str, int],
        video_props: Dict[str, Any],
        fps: int,
        quality: int,
        actual_width: int,
        actual_height: int,
        source_type: str,
        frame_counter: int,
        camera_location: str,
        read_time: float
    ):
        """Process frame and send to Redis asynchronously.

        Features frame optimization to skip encoding for similar frames.

        Args:
            frame: Frame data
            stream_key: Stream identifier
            stream_group_key: Stream group identifier
            topic: Topic name
            source: Video source
            video_props: Video properties
            fps: Target FPS
            quality: JPEG quality
            actual_width: Frame width
            actual_height: Frame height
            source_type: Type of source
            frame_counter: Current frame number
            camera_location: Camera location
            read_time: Time taken to read frame
        """
        frame_start = time.time()

        # Build metadata
        metadata = self.message_builder.build_frame_metadata(
            source, video_props, fps, quality, actual_width, actual_height,
            source_type, frame_counter, False, None, None, camera_location
        )
        metadata["feed_type"] = "disk" if source_type == "video_file" else "camera"
        metadata["frame_count"] = 1
        metadata["stream_unit"] = "frame"

        # Check frame similarity BEFORE encoding (saves CPU if frame is similar)
        is_similar, similarity_score = self.frame_optimizer.is_similar(frame, stream_key)
        reference_frame_id = self._last_sent_frame_ids.get(stream_key)

        # Get timing stats
        last_read, last_write, last_process = self.statistics.get_timing(stream_key)
        input_order = self.statistics.get_next_input_order(stream_key)

        if is_similar and reference_frame_id:
            # Frame is similar to previous - send message with empty content + cached_frame_id
            encoding_time = 0.0  # No encoding needed
            metadata["similarity_score"] = similarity_score

            # Build message with empty content and cached_frame_id
            message = self.message_builder.build_message(
                frame_data=b"",  # EMPTY content for cached frame
                stream_key=stream_key,
                stream_group_key=stream_group_key,
                codec="cached",  # Special codec to indicate cached frame
                metadata=metadata,
                topic=topic,
                broker_config=self.stream_config.get('bootstrap_servers', 'localhost:9092'),
                input_order=input_order,
                last_read_time=last_read,
                last_write_time=last_write,
                last_process_time=last_process,
                cached_frame_id=reference_frame_id,  # Reference to cached frame
            )

            # Send to Redis asynchronously
            write_start = time.time()
            await self.redis_client.add_message(topic, message)
            write_time = time.time() - write_start

            # Update statistics - frame was skipped (no encoding)
            self.statistics.increment_frames_skipped()
            process_time = read_time + write_time
            encoding_time = 0.0  # No encoding for cached frames
            self.statistics.update_timing(stream_key, read_time, write_time, process_time, 0, encoding_time)

            # Track total frame time for metrics
            total_frame_time = time.time() - frame_start
            self._frame_times.append(total_frame_time)
            return

        # Frame is different - encode and send full frame
        encoding_start = time.time()
        frame_data, codec = await self._encode_frame_async(frame, quality)
        encoding_time = time.time() - encoding_start
        metadata["encoding_type"] = "jpeg"

        # Build message (normal frame - no cache reference)
        message = self.message_builder.build_message(
            frame_data, stream_key, stream_group_key, codec, metadata, topic,
            self.stream_config.get('bootstrap_servers', 'localhost:9092'),
            input_order, last_read, last_write, last_process,
            cached_frame_id=None,  # Normal frame, no cache reference
        )

        # Send to Redis asynchronously
        write_start = time.time()
        await self.redis_client.add_message(topic, message)
        write_time = time.time() - write_start

        # Track this frame_id as the last sent for future reference frames
        new_frame_id = message.get("frame_id")
        if new_frame_id:
            self._last_sent_frame_ids[stream_key] = new_frame_id
            self.frame_optimizer.set_last_frame_id(stream_key, new_frame_id)

        # Update statistics
        self.statistics.increment_frames_sent()
        process_time = read_time + write_time
        frame_size = len(frame_data) if frame_data else 0
        self.statistics.update_timing(stream_key, read_time, write_time, process_time, frame_size, encoding_time)

        # Track total frame time for metrics
        total_frame_time = time.time() - frame_start
        self._frame_times.append(total_frame_time)

    async def _encode_frame_async(self, frame, quality: int) -> tuple:
        """Encode frame to JPEG.

        Encoding is done inline (synchronously) because:
        1. cv2.imencode() is very fast (~5ms for 480p)
        2. cv2.imencode() releases the GIL, allowing other async tasks to run
        3. Executor overhead (queue, context switch) adds more latency than the encoding itself
        4. At 1000 cameras, executor queue contention causes 200ms+ delays

        Args:
            frame: Frame data (numpy array)
            quality: JPEG quality

        Returns:
            Tuple of (encoded_data, codec)
        """
        encode_start = time.time()

        try:
            # Encode directly - cv2.imencode releases GIL so other coroutines can run
            encode_success, jpeg_buffer = cv2.imencode(
                '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            )

            encoding_time = time.time() - encode_start
            self._encoding_times.append(encoding_time)
            self._frames_encoded += 1

            # Periodically log metrics
            if time.time() - self._last_metrics_log > self._metrics_log_interval:
                self._last_metrics_log = time.time()
                await self._log_metrics()

            if encode_success:
                # Return buffer directly
                frame_data = memoryview(jpeg_buffer)
                return frame_data, "h264"
            else:
                # Encoding failed - return raw frame
                self.logger.warning(f"Worker {self.worker_id}: JPEG encoding returned False, using raw frame")
                frame_data = memoryview(frame).cast('B')
                return frame_data, "raw"

        except Exception as exc:
            self._encoding_errors += 1
            encoding_time = time.time() - encode_start

            self.logger.error(
                f"Worker {self.worker_id}: Encoding error: {type(exc).__name__}: {exc} "
                f"(encoding time: {encoding_time*1000:.2f}ms)",
                exc_info=True
            )
            raise

    # ========================================================================
    # Dynamic Camera Management Methods
    # ========================================================================

    async def _command_handler(self):
        """Process commands from the manager (runs in async loop)."""
        self.logger.info(f"Worker {self.worker_id}: Command handler started")

        while not self.stop_event.is_set():
            try:
                # Non-blocking check for commands using executor
                command = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._get_command_nonblocking
                )

                if command:
                    await self._process_command(command)
                else:
                    # Small sleep when no commands to avoid busy-waiting
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                self.logger.info(f"Worker {self.worker_id}: Command handler cancelled")
                break
            except Exception as exc:
                self.logger.error(f"Worker {self.worker_id}: Error in command handler: {exc}", exc_info=True)
                await asyncio.sleep(1.0)

        self.logger.info(f"Worker {self.worker_id}: Command handler stopped")

    def _get_command_nonblocking(self):
        """Get command from queue without blocking."""
        try:
            return self.command_queue.get_nowait()
        except Exception:
            return None

    async def _process_command(self, command: Dict[str, Any]):
        """Process a single command.

        Args:
            command: Command dictionary with 'type' and payload
        """
        cmd_type = command.get('type')
        self.logger.info(f"Worker {self.worker_id}: Processing command: {cmd_type}")

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
                # Update = remove + add with new config
                await self._remove_camera_internal(stream_key)
                success = await self._add_camera_internal(camera_config)
                self._send_response(cmd_type, stream_key, success)

            else:
                self.logger.warning(f"Worker {self.worker_id}: Unknown command type: {cmd_type}")

        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Error processing command {cmd_type}: {exc}", exc_info=True)
            self._send_response(cmd_type, command.get('stream_key'), False, str(exc))

    async def _add_camera_internal(self, camera_config: Dict[str, Any]) -> bool:
        """Add a camera and start its streaming task.

        Args:
            camera_config: Camera configuration dictionary

        Returns:
            bool: True if camera was added successfully
        """
        stream_key = camera_config.get('stream_key')

        if not stream_key:
            self.logger.error(f"Worker {self.worker_id}: Camera config missing stream_key")
            return False

        if stream_key in self.camera_tasks:
            self.logger.warning(f"Worker {self.worker_id}: Camera {stream_key} already exists")
            return False

        try:
            # Create and start camera task
            task = asyncio.create_task(
                self._camera_handler(camera_config),
                name=f"camera-{stream_key}"
            )
            self.camera_tasks[stream_key] = task

            self.logger.info(f"Worker {self.worker_id}: Added camera {stream_key}")
            return True

        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Failed to add camera {stream_key}: {exc}", exc_info=True)
            return False

    async def _remove_camera_internal(self, stream_key: str) -> bool:
        """Remove a camera and stop its streaming task.

        Args:
            stream_key: Unique identifier for the camera stream

        Returns:
            bool: True if camera was removed successfully
        """
        if stream_key not in self.camera_tasks:
            self.logger.warning(f"Worker {self.worker_id}: Camera {stream_key} not found")
            return False

        try:
            # Cancel the camera task
            task = self.camera_tasks[stream_key]
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

            # Remove from tracking
            del self.camera_tasks[stream_key]

            # Release capture if exists
            if stream_key in self.captures:
                self.captures[stream_key].release()
                del self.captures[stream_key]

            self.logger.info(f"Worker {self.worker_id}: Removed camera {stream_key}")
            return True

        except Exception as exc:
            self.logger.error(f"Worker {self.worker_id}: Error removing camera {stream_key}: {exc}", exc_info=True)
            return False

    def _send_response(self, cmd_type: str, stream_key: str, success: bool, error: str = None):
        """Send response back to manager.

        Args:
            cmd_type: Type of command that was processed
            stream_key: Stream key the command was for
            success: Whether the command succeeded
            error: Error message if failed
        """
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
                self.logger.warning(f"Worker {self.worker_id}: Failed to send response: {exc}", exc_info=True)

    async def _shutdown(self):
        """Gracefully shutdown worker - cancel tasks and cleanup."""
        self.logger.info(f"Worker {self.worker_id}: Starting graceful shutdown")

        # Cancel all camera tasks
        for stream_key, task in self.camera_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"Worker {self.worker_id}: Cancelled task for {stream_key}")

        # Wait for tasks to complete
        if self.camera_tasks:
            await asyncio.gather(*self.camera_tasks.values(), return_exceptions=True)

        # Release all captures
        for stream_key, cap in list(self.captures.items()):
            cap.release()
            self.logger.info(f"Worker {self.worker_id}: Released capture {stream_key}")
        self.captures.clear()

        # Close Redis client
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info(f"Worker {self.worker_id}: Closed Redis client")

        # Shutdown capture executor
        self.logger.info(f"Worker {self.worker_id}: Shutting down capture executor...")
        try:
            self.capture_executor.shutdown(wait=True, cancel_futures=False)
        except Exception as exc:
            self.logger.warning(f"Worker {self.worker_id}: Error shutting down capture pool: {exc}", exc_info=True)
        self.logger.info(f"Worker {self.worker_id}: Capture executor shut down")

        # Report final health
        self._report_health("stopped")

        self.logger.info(f"Worker {self.worker_id}: Shutdown complete")

    def _report_health(self, status: str, active_cameras: int = 0, error: Optional[str] = None):
        """Report health status to main process.

        Args:
            status: Worker status (running, stopped, error)
            active_cameras: Number of active camera tasks
            error: Error message if status is error
        """
        try:
            # Get CPU/memory metrics for this process
            proc_cpu = 0
            proc_memory_mb = 0
            try:
                proc_cpu = self._process_info.cpu_percent(interval=None)
                proc_memory_mb = self._process_info.memory_info().rss / 1024 / 1024
            except Exception:
                pass

            # Calculate average encoding time
            avg_encoding_ms = 0
            if self._encoding_times:
                avg_encoding_ms = sum(self._encoding_times) / len(self._encoding_times) * 1000

            # Collect per-camera statistics for metrics reporting
            per_camera_stats = {}
            for stream_key in self.camera_tasks.keys():
                try:
                    timing_stats = self.statistics.get_timing_statistics(stream_key)
                    if timing_stats:
                        per_camera_stats[stream_key] = {
                            'fps': timing_stats.get('fps', {}),
                            'read_time_ms': timing_stats.get('read_time_ms', {}),
                            'write_time_ms': timing_stats.get('write_time_ms', {}),
                            'encoding_time_ms': timing_stats.get('encoding_time_ms', {}),
                            'frame_size_bytes': timing_stats.get('frame_size_bytes', {}),
                        }
                except Exception:
                    pass

            health_report = {
                'worker_id': self.worker_id,
                'status': status,
                'active_cameras': active_cameras,
                'timestamp': time.time(),
                'error': error,
                # Extended metrics for debugging
                'metrics': {
                    'cpu_percent': proc_cpu,
                    'memory_mb': proc_memory_mb,
                    'frames_encoded': self._frames_encoded,
                    'encoding_errors': self._encoding_errors,
                    'avg_encoding_ms': avg_encoding_ms,
                    'encoding_processes': self.num_encoding_processes,
                    'capture_threads': self.num_capture_threads,
                },
                # Per-camera statistics for metrics reporting
                'per_camera_stats': per_camera_stats,
            }
            self.health_queue.put_nowait(health_report)
        except Exception as exc:
            self.logger.warning(f"Worker {self.worker_id}: Failed to report health: {exc}", exc_info=True)


def _encode_frame_worker(frame, quality: int):
    """Worker function for encoding frames in process pool.

    This runs in a separate process for true parallel execution.

    Args:
        frame: Frame data (numpy array)
        quality: JPEG quality

    Returns:
        Tuple of (success, encoded_buffer)
    """
    import cv2
    return cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


def run_async_worker(
    worker_id: int,
    camera_configs: List[Dict[str, Any]],
    stream_config: Dict[str, Any],
    stop_event: multiprocessing.Event,
    health_queue: multiprocessing.Queue,
    command_queue: multiprocessing.Queue = None,
    response_queue: multiprocessing.Queue = None
):
    """Entry point for async worker process.

    This function is called by multiprocessing.Process to start a worker.

    Args:
        worker_id: Worker identifier
        camera_configs: List of camera configurations
        stream_config: Streaming configuration
        stop_event: Shutdown event
        health_queue: Health reporting queue
        command_queue: Queue for receiving dynamic camera commands
        response_queue: Queue for sending command responses
    """
    # Setup logging for this process
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - Worker-{worker_id} - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(f"AsyncWorker-{worker_id}")
    logger.info(f"Starting async worker {worker_id}")
    import os
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["KMP_NUM_THREADS"] = "1"
    os.environ["KMP_BLOCKTIME"] = "0"
    os.environ["TBB_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    import cv2
    cv2.setNumThreads(1)
    cv2.setUseOptimized(True)
    cv2.ocl.setUseOpenCL(False)
    try:
        # Create worker
        worker = AsyncCameraWorker(
            worker_id=worker_id,
            camera_configs=camera_configs,
            stream_config=stream_config,
            stop_event=stop_event,
            health_queue=health_queue,
            command_queue=command_queue,
            response_queue=response_queue
        )

        # Run event loop
        asyncio.run(worker.run())

    except Exception as exc:
        logger.error(f"Worker {worker_id} failed: {exc}", exc_info=True)
        raise
