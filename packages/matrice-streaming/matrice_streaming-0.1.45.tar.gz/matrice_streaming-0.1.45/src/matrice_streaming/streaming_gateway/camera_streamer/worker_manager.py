"""Worker manager for coordinating multiple async camera workers.

This module manages a pool of async worker processes, distributing cameras
across them and monitoring their health.
"""
import logging
import multiprocessing
import os
import sys
import time
import signal
from typing import List, Dict, Any, Optional
from pathlib import Path

from .async_camera_worker import run_async_worker
from .encoding_pool_manager import EncodingPoolManager
from .camera_streamer import CameraStreamer


class WorkerManager:
    """Manages multiple async camera worker processes with dynamic scaling.

    This manager coordinates worker processes based on available CPU cores,
    distributing cameras across them for optimal throughput. Each worker handles
    multiple cameras concurrently using async I/O.
    """

    def __init__(
        self,
        camera_configs: List[Dict[str, Any]],
        stream_config: Dict[str, Any],
        num_workers: Optional[int] = None,
        cpu_percentage: float = 0.9,
        num_encoding_workers: Optional[int] = None,
        max_cameras_per_worker: int = 100
    ):
        """Initialize worker manager with dynamic CPU-based scaling.

        Args:
            camera_configs: List of all camera configurations
            stream_config: Streaming configuration (Redis, Kafka, etc.)
            num_workers: Number of worker processes (default: auto-calculated from CPU cores)
            cpu_percentage: Percentage of CPU cores to use (default: 0.9 = 90%)
            num_encoding_workers: Number of encoding workers (default: CPU_count - 2)
            max_cameras_per_worker: Maximum cameras per worker for load balancing (default: 100)
        """
        self.camera_configs = camera_configs
        self.stream_config = stream_config

        # Calculate dynamic worker count based on CPU cores if not specified
        if num_workers is None:
            cpu_count = os.cpu_count() or 4  # Fallback to 4 if can't detect
            num_cameras = len(camera_configs)

            # For systems with 16+ cores OR large camera counts, use camera-based calculation
            # This applies to Docker containers with limited CPU allocation (e.g., 20 cores)
            # Too many workers = process overhead; too few = underutilization
            # Target: ~25 cameras per worker for better read parallelism with video files
            if cpu_count >= 16 or num_cameras >= 100:
                # Use camera-based calculation for better distribution
                # 1000 cameras / 25 cameras per worker = 40 workers
                target_cameras_per_worker = 25
                calculated_workers = max(4, min(num_cameras // target_cameras_per_worker, 50))
            else:
                # Standard calculation for smaller systems
                calculated_workers = max(4, int(cpu_count * cpu_percentage))

            # Cap at camera count (no point having more workers than cameras)
            self.num_workers = min(calculated_workers, num_cameras) if num_cameras > 0 else calculated_workers
        else:
            self.num_workers = num_workers

        self.num_encoding_workers = num_encoding_workers
        self.logger = logging.getLogger(__name__)

        # Max cameras per worker (for load balancing)
        self.max_cameras_per_worker = max_cameras_per_worker

        # Log dynamic scaling info
        cpu_count = os.cpu_count() or 4
        self.logger.info(
            f"Dynamic worker scaling: {cpu_count} CPU cores detected, "
            f"using {cpu_percentage*100:.0f}% = {self.num_workers} workers "
            f"for {len(camera_configs)} cameras"
        )

        # Note: Batch parameters are calculated per-worker in _start_worker()
        # based on each worker's camera count, not the global total.
        # This ensures optimal batching when cameras are distributed across workers.

        # Multiprocessing primitives
        self.stop_event = multiprocessing.Event()
        self.health_queue = multiprocessing.Queue()

        # Worker processes
        self.workers: List[multiprocessing.Process] = []
        self.worker_camera_assignments: Dict[int, List[Dict[str, Any]]] = {}

        # Encoding pool
        self.encoding_pool_manager: Optional[EncodingPoolManager] = None
        self.encoding_pool: Optional[multiprocessing.Pool] = None

        # Health monitoring
        self.last_health_reports: Dict[int, Dict[str, Any]] = {}

        # Dynamic camera support - command queues for each worker
        self.command_queues: Dict[int, multiprocessing.Queue] = {}

        # Response queue for acknowledgments from workers
        self.response_queue = multiprocessing.Queue()

        # Camera-to-worker mapping for targeted operations
        self.camera_to_worker: Dict[str, int] = {}  # stream_key -> worker_id

        # Worker load tracking
        self.worker_camera_count: Dict[int, int] = {}  # worker_id -> camera_count

        self.logger.info(
            f"WorkerManager initialized: {self.num_workers} workers, "
            f"{len(camera_configs)} cameras total, "
            f"max {self.max_cameras_per_worker} cameras per worker"
        )

    def start(self):
        """Start all workers and begin streaming."""
        try:
            # Distribute cameras across workers (static partitioning)
            self._distribute_cameras()

            # Note: Encoding pool not needed - each worker uses asyncio.to_thread()
            # which provides good enough parallelism for JPEG encoding (mostly C code)

            # Start worker processes
            self.logger.info(f"Starting {self.num_workers} worker processes...")
            for worker_id in range(self.num_workers):
                self._start_worker(worker_id)

            self.logger.info(
                f"All workers started! "
                f"Streaming {len(self.camera_configs)} cameras across {self.num_workers} workers"
            )

        except Exception as exc:
            self.logger.error(f"Failed to start workers: {exc}")
            self.stop()
            raise

    def _distribute_cameras(self):
        """Distribute cameras across workers using static partitioning."""
        total_cameras = len(self.camera_configs)
        cameras_per_worker = total_cameras // self.num_workers
        remainder = total_cameras % self.num_workers

        self.logger.info(
            f"Distributing {total_cameras} cameras: "
            f"~{cameras_per_worker} per worker"
        )

        camera_idx = 0
        for worker_id in range(self.num_workers):
            # Some workers get 1 extra camera if there's a remainder
            num_cameras = cameras_per_worker + (1 if worker_id < remainder else 0)

            worker_cameras = self.camera_configs[camera_idx:camera_idx + num_cameras]
            self.worker_camera_assignments[worker_id] = worker_cameras

            self.logger.info(
                f"Worker {worker_id}: {len(worker_cameras)} cameras "
                f"(indices {camera_idx} to {camera_idx + num_cameras - 1})"
            )

            camera_idx += num_cameras

    def _start_worker(self, worker_id: int):
        """Start a single worker process with command queue for dynamic camera support.

        Args:
            worker_id: Worker identifier
        """
        worker_cameras = self.worker_camera_assignments.get(worker_id, [])

        # Create command queue for this worker (even if no cameras assigned initially)
        command_queue = multiprocessing.Queue()
        self.command_queues[worker_id] = command_queue

        # Track initial camera count
        self.worker_camera_count[worker_id] = len(worker_cameras)

        # Track initial camera-to-worker mapping
        for cam_config in worker_cameras:
            stream_key = cam_config.get('stream_key')
            if stream_key:
                self.camera_to_worker[stream_key] = worker_id

        if not worker_cameras:
            self.logger.warning(f"Worker {worker_id} has no cameras assigned initially")

        # Calculate batch parameters based on THIS worker's camera count, not global total
        # Each worker only handles ~50 cameras (1000 / 20 workers), so batch settings
        # should match the per-worker load, not the overall deployment size
        worker_stream_config = self.stream_config.copy()
        num_worker_cameras = len(worker_cameras)
        if num_worker_cameras > 0 and worker_stream_config.get('enable_batching', True):
            batch_params = CameraStreamer.calculate_batch_parameters(num_worker_cameras)
            worker_stream_config.update({
                'enable_batching': True,
                'batch_size': batch_params['batch_size'],
                'batch_timeout': batch_params['batch_timeout']
            })
            self.logger.debug(
                f"Worker {worker_id}: {num_worker_cameras} cameras → "
                f"batch_size={batch_params['batch_size']}, "
                f"batch_timeout={batch_params['batch_timeout']*1000:.1f}ms"
            )

        try:
            # Use 'fork' context on Linux to avoid re-importing modules in child processes.
            # This prevents dependencies_check from running pip install in child processes.
            # On Windows, 'fork' is not available so we use 'spawn' (the only option).
            if sys.platform == 'win32':
                # Windows only supports spawn
                ctx = multiprocessing.get_context('spawn')
                context_name = 'spawn'
            else:
                # Linux/macOS: use 'fork' - child inherits parent memory, no re-imports
                ctx = multiprocessing.get_context('fork')
                context_name = 'fork'

            worker = ctx.Process(
                target=run_async_worker,
                args=(
                    worker_id,
                    worker_cameras,
                    worker_stream_config,  # Use per-worker config with correct batch params
                    self.stop_event,
                    self.health_queue,
                    command_queue,        # Pass command queue for dynamic camera ops
                    self.response_queue   # Pass response queue for acknowledgments
                ),
                name=f"AsyncWorker-{worker_id}",
                daemon=False  # Non-daemon so we can properly wait for shutdown
            )
            worker.start()
            self.workers.append(worker)

            self.logger.info(
                f"Started worker {worker_id} (PID: {worker.pid}) "
                f"with {len(worker_cameras)} cameras (context: {context_name})"
            )

        except Exception as exc:
            self.logger.error(f"Failed to start worker {worker_id}: {exc}")
            raise

    def monitor(self, duration: Optional[float] = None):
        """Monitor workers and collect health reports.

        Args:
            duration: How long to monitor (None = indefinite)
        """
        self.logger.info("Starting health monitoring...")

        start_time = time.time()
        last_summary_time = start_time

        try:
            while not self.stop_event.is_set():
                # Check if duration exceeded
                if duration and (time.time() - start_time) >= duration:
                    self.logger.info(f"Monitoring duration ({duration}s) complete")
                    break

                # Collect health reports
                while not self.health_queue.empty():
                    try:
                        report = self.health_queue.get_nowait()
                        worker_id = report['worker_id']
                        self.last_health_reports[worker_id] = report

                        # Log significant status changes
                        if report['status'] in ['error', 'stopped']:
                            self.logger.warning(
                                f"Worker {worker_id} status: {report['status']}"
                                f" (error: {report.get('error', 'None')})"
                            )

                    except Exception as exc:
                        self.logger.error(f"Error processing health report: {exc}")

                # Check worker processes
                for i, worker in enumerate(self.workers):
                    if not worker.is_alive() and not self.stop_event.is_set():
                        self.logger.error(
                            f"Worker {i} (PID: {worker.pid}) died unexpectedly! "
                            f"Exit code: {worker.exitcode}"
                        )

                # Print summary every 10 seconds
                if time.time() - last_summary_time >= 10.0:
                    self._print_health_summary()
                    last_summary_time = time.time()

                time.sleep(0.5)

        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")

    def _print_health_summary(self):
        """Print summary of worker health."""
        running_workers = sum(1 for w in self.workers if w.is_alive())
        total_cameras = sum(
            report.get('active_cameras', 0)
            for report in self.last_health_reports.values()
        )

        self.logger.info(
            f"Health Summary: {running_workers}/{len(self.workers)} workers alive, "
            f"{total_cameras} active cameras"
        )

        # Detailed per-worker status
        for worker_id, report in sorted(self.last_health_reports.items()):
            status = report.get('status', 'unknown')
            cameras = report.get('active_cameras', 0)
            age = time.time() - report.get('timestamp', 0)

            self.logger.debug(
                f"  Worker {worker_id}: {status}, {cameras} cameras, "
                f"last report {age:.1f}s ago"
            )

    def stop(self, timeout: float = 15.0):
        """Stop all workers gracefully.

        Args:
            timeout: Maximum time to wait per worker (seconds)
        """
        self.logger.info("Stopping all workers...")

        # Signal stop
        self.stop_event.set()

        # Wait for workers to finish
        for i, worker in enumerate(self.workers):
            if worker.is_alive():
                self.logger.info(f"Waiting for worker {i} to stop...")
                worker.join(timeout=timeout)

                if worker.is_alive():
                    self.logger.warning(
                        f"Worker {i} did not stop gracefully, terminating..."
                    )
                    worker.terminate()
                    worker.join(timeout=5.0)

                    if worker.is_alive():
                        self.logger.error(f"Worker {i} could not be stopped!")
                    else:
                        self.logger.info(f"Worker {i} terminated")
                else:
                    self.logger.info(f"Worker {i} stopped gracefully")

        # Final summary
        self.logger.info("="*60)
        self.logger.info("SHUTDOWN COMPLETE")
        self.logger.info("="*60)
        self._print_final_summary()

    def _print_final_summary(self):
        """Print final summary of worker status."""
        total_cameras_assigned = sum(
            len(cameras)
            for cameras in self.worker_camera_assignments.values()
        )

        self.logger.info(f"Total cameras assigned: {total_cameras_assigned}")
        self.logger.info(f"Workers started: {len(self.workers)}")

        # Count workers by exit status
        normal_exits = sum(1 for w in self.workers if w.exitcode == 0)
        error_exits = sum(1 for w in self.workers if w.exitcode != 0 and w.exitcode is not None)
        still_alive = sum(1 for w in self.workers if w.is_alive())

        self.logger.info(
            f"Exit status: {normal_exits} normal, {error_exits} errors, "
            f"{still_alive} still alive"
        )

        # Last health reports
        if self.last_health_reports:
            self.logger.info("Last health reports:")
            for worker_id in sorted(self.last_health_reports.keys()):
                report = self.last_health_reports[worker_id]
                self.logger.info(
                    f"  Worker {worker_id}: {report['status']}, "
                    f"{report.get('active_cameras', 0)} cameras"
                )

    def run(self, duration: Optional[float] = None):
        """Start workers and monitor until stopped.

        This is the main entry point that combines start(), monitor(), and stop().

        Args:
            duration: How long to run (None = until interrupted)
        """
        try:
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Start all workers
            self.start()

            # Monitor
            self.monitor(duration=duration)

        except Exception as exc:
            self.logger.error(f"Error in run loop: {exc}", exc_info=True)

        finally:
            # Always cleanup
            self.stop()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.stop_event.set()

    # ========================================================================
    # Dynamic Camera Management Methods
    # ========================================================================

    def add_camera(self, camera_config: Dict[str, Any]) -> bool:
        """Add a camera to the least-loaded worker at runtime.

        Args:
            camera_config: Camera configuration dictionary with stream_key, source, etc.

        Returns:
            bool: True if camera was added successfully
        """
        stream_key = camera_config.get('stream_key')

        if not stream_key:
            self.logger.error("Camera config missing stream_key")
            return False

        if stream_key in self.camera_to_worker:
            self.logger.warning(f"Camera {stream_key} already exists, use update_camera instead")
            return False

        # Find least-loaded worker that's not at capacity
        target_worker_id = self._find_least_loaded_worker()

        if target_worker_id is None:
            self.logger.error("All workers at capacity, cannot add camera")
            return False

        # Send command to worker
        command = {
            'type': 'add_camera',
            'camera_config': camera_config,
            'timestamp': time.time()
        }

        try:
            self.command_queues[target_worker_id].put(command, timeout=5.0)

            # Update tracking (optimistic - will be verified via health report)
            self.camera_to_worker[stream_key] = target_worker_id
            self.worker_camera_count[target_worker_id] += 1

            self.logger.info(
                f"Sent add_camera command for {stream_key} to worker {target_worker_id}"
            )
            return True

        except Exception as exc:
            self.logger.error(f"Failed to send add_camera command: {exc}")
            return False

    def remove_camera(self, stream_key: str) -> bool:
        """Remove a camera from its assigned worker.

        Args:
            stream_key: Unique identifier for the camera stream

        Returns:
            bool: True if camera removal was initiated
        """
        if stream_key not in self.camera_to_worker:
            self.logger.warning(f"Camera {stream_key} not found in any worker")
            return False

        worker_id = self.camera_to_worker[stream_key]

        command = {
            'type': 'remove_camera',
            'stream_key': stream_key,
            'timestamp': time.time()
        }

        try:
            self.command_queues[worker_id].put(command, timeout=5.0)

            # Update tracking
            del self.camera_to_worker[stream_key]
            self.worker_camera_count[worker_id] -= 1

            self.logger.info(
                f"Sent remove_camera command for {stream_key} to worker {worker_id}"
            )
            return True

        except Exception as exc:
            self.logger.error(f"Failed to send remove_camera command: {exc}")
            return False

    def update_camera(self, camera_config: Dict[str, Any]) -> bool:
        """Update a camera's configuration (removes and re-adds with new config).

        Args:
            camera_config: Updated camera configuration

        Returns:
            bool: True if update was initiated
        """
        stream_key = camera_config.get('stream_key')

        if not stream_key:
            self.logger.error("Camera config missing stream_key")
            return False

        if stream_key not in self.camera_to_worker:
            self.logger.warning(f"Camera {stream_key} not found, adding instead")
            return self.add_camera(camera_config)

        worker_id = self.camera_to_worker[stream_key]

        command = {
            'type': 'update_camera',
            'camera_config': camera_config,
            'stream_key': stream_key,
            'timestamp': time.time()
        }

        try:
            self.command_queues[worker_id].put(command, timeout=5.0)
            self.logger.info(
                f"Sent update_camera command for {stream_key} to worker {worker_id}"
            )
            return True

        except Exception as exc:
            self.logger.error(f"Failed to send update_camera command: {exc}")
            return False

    def _find_least_loaded_worker(self) -> Optional[int]:
        """Find the worker with the least cameras that's not at capacity.

        Returns:
            Worker ID or None if all workers are at capacity
        """
        # Filter workers that have capacity and are alive
        available_workers = []
        for worker_id, count in self.worker_camera_count.items():
            if count < self.max_cameras_per_worker and worker_id in self.command_queues:
                # Check if worker is still alive
                if worker_id < len(self.workers) and self.workers[worker_id].is_alive():
                    available_workers.append((worker_id, count))

        if not available_workers:
            return None

        # Return worker with minimum cameras
        return min(available_workers, key=lambda x: x[1])[0]

    def get_camera_assignments(self) -> Dict[str, int]:
        """Get current camera-to-worker assignments.

        Returns:
            Dict mapping stream_key to worker_id
        """
        return self.camera_to_worker.copy()

    def _flush_health_queue(self):
        """Consume all pending health reports from the queue."""
        while not self.health_queue.empty():
            try:
                report = self.health_queue.get_nowait()
                worker_id = report.get('worker_id')
                if worker_id is not None:
                    self.last_health_reports[worker_id] = report
            except Exception:
                break

    def get_worker_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about workers and cameras.

        Returns:
            Dict with worker statistics for metrics/monitoring
        """
        # First, flush all pending health reports from the queue
        self._flush_health_queue()

        # Aggregate per-camera stats from all worker health reports
        per_camera_stats = {}
        for worker_id, report in self.last_health_reports.items():
            worker_camera_stats = report.get('per_camera_stats', {})
            per_camera_stats.update(worker_camera_stats)

        return {
            'num_workers': len(self.workers),
            'running_workers': sum(1 for w in self.workers if w.is_alive()),
            'total_cameras': sum(self.worker_camera_count.values()),
            'camera_assignments': self.camera_to_worker.copy(),
            'worker_camera_counts': self.worker_camera_count.copy(),
            'health_reports': {
                worker_id: {
                    'status': report.get('status', 'unknown'),
                    'active_cameras': report.get('active_cameras', 0),
                    'timestamp': report.get('timestamp', 0),
                    'metrics': report.get('metrics', {}),
                }
                for worker_id, report in self.last_health_reports.items()
            },
            'per_camera_stats': per_camera_stats,
        }

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
