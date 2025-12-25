"""Worker manager for coordinating multiple GStreamer async camera workers.

This module manages a pool of GStreamer worker processes, distributing cameras
across them for hardware-accelerated video encoding.
"""
import logging
import multiprocessing
import os
import sys
import time
import signal
from typing import List, Dict, Any, Optional

from .gstreamer_worker import run_gstreamer_worker, is_gstreamer_available
from .camera_streamer import CameraStreamer


class GStreamerWorkerManager:
    """Manages multiple GStreamer async camera worker processes.
    
    This manager coordinates worker processes using GStreamer pipelines
    for efficient hardware/software video encoding. It follows the same
    API as WorkerManager for drop-in replacement.
    """
    
    def __init__(
        self,
        camera_configs: List[Dict[str, Any]],
        stream_config: Dict[str, Any],
        num_workers: Optional[int] = None,
        cpu_percentage: float = 0.9,
        max_cameras_per_worker: int = 100,
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
        """Initialize GStreamer worker manager.

        Args:
            camera_configs: List of all camera configurations
            stream_config: Streaming configuration (Redis, Kafka, etc.)
            num_workers: Number of worker processes (auto-calculated if None)
            cpu_percentage: Percentage of CPU cores to use (default: 90%)
            max_cameras_per_worker: Maximum cameras per worker
            gstreamer_encoder: Encoder type (auto, nvenc, x264, openh264, jpeg)
            gstreamer_codec: Codec (h264, h265)
            gstreamer_preset: NVENC preset
            gpu_id: GPU device ID for NVENC
            platform: Platform override (auto, jetson, desktop-gpu, intel, amd, cpu)
            use_hardware_decode: Enable hardware decode
            use_hardware_jpeg: Enable hardware JPEG encoding
            jetson_use_nvmm: Use NVMM zero-copy on Jetson
            frame_optimizer_mode: Frame optimization mode (hash-only, dual-appsink, disabled)
            fallback_on_error: Fallback to CPU pipeline on errors
            verbose_pipeline_logging: Enable verbose pipeline logging
        """
        if not is_gstreamer_available():
            raise RuntimeError(
                "GStreamer not available. Install with: "
                "pip install PyGObject && apt-get install gstreamer1.0-plugins-*"
            )
            
        self.camera_configs = camera_configs
        self.stream_config = stream_config
        self.gstreamer_encoder = gstreamer_encoder
        self.gstreamer_codec = gstreamer_codec
        self.gstreamer_preset = gstreamer_preset
        self.gpu_id = gpu_id
        # Platform-specific settings
        self.platform = platform
        self.use_hardware_decode = use_hardware_decode
        self.use_hardware_jpeg = use_hardware_jpeg
        self.jetson_use_nvmm = jetson_use_nvmm
        self.frame_optimizer_mode = frame_optimizer_mode
        self.fallback_on_error = fallback_on_error
        self.verbose_pipeline_logging = verbose_pipeline_logging

        # Platform detection (NEW)
        from .device_detection import PlatformDetector, PlatformType
        self.platform_detector = PlatformDetector.get_instance()
        self.platform_info = self.platform_detector.detect()

        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"Detected platform: {self.platform_info.platform_type.value}, "
            f"Model: {self.platform_info.model}"
        )

        # Platform-aware worker calculation (NEW)
        if num_workers is None:
            cpu_count = os.cpu_count() or 4
            num_cameras = len(camera_configs)

            # Adjust based on platform capabilities
            if self.platform_info.platform_type == PlatformType.JETSON:
                # Jetson has fewer cores, limit workers
                # Hardware encoding means each worker can handle more cameras
                target_per_worker = 30  # Jetson HW encoding is efficient
                calculated = max(4, min(num_cameras // target_per_worker, 8))
                self.logger.info(f"Jetson platform: limiting to max 8 workers")

            elif self.platform_info.platform_type in (PlatformType.INTEL_GPU, PlatformType.AMD_GPU):
                # VAAPI acceleration, moderate parallelism
                target_per_worker = 25
                calculated = max(4, min(num_cameras // target_per_worker, 16))

            elif self.platform_info.platform_type == PlatformType.DESKTOP_NVIDIA_GPU:
                # Desktop GPU, good parallelism
                if cpu_count >= 16 or num_cameras >= 100:
                    target_per_worker = 25
                    calculated = max(4, min(num_cameras // target_per_worker, 50))
                else:
                    calculated = max(4, int(cpu_count * cpu_percentage))

            else:  # CPU-only
                # CPU-only needs more workers for parallelism
                calculated = max(4, int(cpu_count * cpu_percentage))

            self.num_workers = min(calculated, num_cameras) if num_cameras > 0 else calculated
        else:
            self.num_workers = num_workers

        self.max_cameras_per_worker = max_cameras_per_worker

        self.logger.info(
            f"GStreamerWorkerManager: {self.num_workers} workers for {len(camera_configs)} cameras, "
            f"encoder={gstreamer_encoder}, codec={gstreamer_codec}, gpu={gpu_id}"
        )

        # Always use spawn context for GStreamer workers
        # GStreamer has global state that doesn't work well with fork after initialization
        self._mp_ctx = multiprocessing.get_context('spawn')

        # Multiprocessing primitives (using spawn context)
        self.stop_event = self._mp_ctx.Event()
        self.health_queue = self._mp_ctx.Queue()

        # Workers
        self.workers: List[multiprocessing.Process] = []
        self.worker_camera_assignments: Dict[int, List[Dict[str, Any]]] = {}

        # Health monitoring
        self.last_health_reports: Dict[int, Dict[str, Any]] = {}

        # Dynamic camera management
        self.command_queues: Dict[int, multiprocessing.Queue] = {}
        self.response_queue = self._mp_ctx.Queue()
        self.camera_to_worker: Dict[str, int] = {}
        self.worker_camera_count: Dict[int, int] = {}
        
    def start(self):
        """Start all workers."""
        try:
            self._distribute_cameras()
            
            self.logger.info(f"Starting {self.num_workers} GStreamer workers...")
            for worker_id in range(self.num_workers):
                self._start_worker(worker_id)
                
            self.logger.info(
                f"All GStreamer workers started! "
                f"Streaming {len(self.camera_configs)} cameras"
            )
            
        except Exception as exc:
            self.logger.error(f"Failed to start workers: {exc}")
            self.stop()
            raise
            
    def _distribute_cameras(self):
        """Distribute cameras across workers."""
        total = len(self.camera_configs)
        per_worker = total // self.num_workers
        remainder = total % self.num_workers
        
        self.logger.info(f"Distributing {total} cameras: ~{per_worker} per worker")
        
        idx = 0
        for worker_id in range(self.num_workers):
            count = per_worker + (1 if worker_id < remainder else 0)
            worker_cameras = self.camera_configs[idx:idx + count]
            self.worker_camera_assignments[worker_id] = worker_cameras
            
            self.logger.info(
                f"GStreamer Worker {worker_id}: {len(worker_cameras)} cameras"
            )
            idx += count
            
    def _start_worker(self, worker_id: int):
        """Start a single GStreamer worker process."""
        worker_cameras = self.worker_camera_assignments.get(worker_id, [])
        
        # Create command queue (using spawn context)
        command_queue = self._mp_ctx.Queue()
        self.command_queues[worker_id] = command_queue
        
        # Track cameras
        self.worker_camera_count[worker_id] = len(worker_cameras)
        for cam in worker_cameras:
            stream_key = cam.get('stream_key')
            if stream_key:
                self.camera_to_worker[stream_key] = worker_id

        # Build worker stream config with optimal batch parameters
        worker_stream_config = self.stream_config.copy()

        # Calculate optimal batch parameters based on per-worker camera count
        num_worker_cameras = len(worker_cameras)
        if num_worker_cameras > 0 and worker_stream_config.get('enable_batching', True):
            batch_params = CameraStreamer.calculate_batch_parameters(num_worker_cameras)
            worker_stream_config.update({
                'enable_batching': True,
                'batch_size': batch_params['batch_size'],
                'batch_timeout': batch_params['batch_timeout']
            })
            self.logger.info(
                f"Worker {worker_id}: Optimized batching for {num_worker_cameras} cameras - "
                f"batch_size={batch_params['batch_size']}, "
                f"batch_timeout={batch_params['batch_timeout']*1000:.1f}ms"
            )

        try:
            # Use the spawn context stored in __init__
            worker = self._mp_ctx.Process(
                target=run_gstreamer_worker,
                args=(
                    worker_id,
                    worker_cameras,
                    worker_stream_config,
                    self.stop_event,
                    self.health_queue,
                    command_queue,
                    self.response_queue,
                    self.gstreamer_encoder,
                    self.gstreamer_codec,
                    self.gstreamer_preset,
                    self.gpu_id,
                    self.platform,
                    self.use_hardware_decode,
                    self.use_hardware_jpeg,
                    self.jetson_use_nvmm,
                    self.frame_optimizer_mode,
                    self.fallback_on_error,
                    self.verbose_pipeline_logging,
                ),
                name=f"GStreamerWorker-{worker_id}",
                daemon=False
            )
            worker.start()
            self.workers.append(worker)
            
            self.logger.info(
                f"Started GStreamer worker {worker_id} (PID: {worker.pid}) "
                f"with {len(worker_cameras)} cameras (context: spawn)"
            )
            
        except Exception as exc:
            self.logger.error(f"Failed to start worker {worker_id}: {exc}")
            raise
            
    def monitor(self, duration: Optional[float] = None):
        """Monitor workers and collect health reports."""
        self.logger.info("Starting GStreamer health monitoring...")
        
        start_time = time.time()
        last_summary_time = start_time
        
        try:
            while not self.stop_event.is_set():
                if duration and (time.time() - start_time) >= duration:
                    break
                    
                # Collect health reports
                while not self.health_queue.empty():
                    try:
                        report = self.health_queue.get_nowait()
                        worker_id = report['worker_id']
                        self.last_health_reports[worker_id] = report
                        
                        if report['status'] in ['error', 'stopped']:
                            self.logger.warning(
                                f"GStreamer Worker {worker_id}: {report['status']} "
                                f"(error: {report.get('error')})"
                            )
                    except Exception as exc:
                        self.logger.error(f"Health report error: {exc}")
                        
                # Check workers
                for i, worker in enumerate(self.workers):
                    if not worker.is_alive() and not self.stop_event.is_set():
                        self.logger.error(
                            f"GStreamer Worker {i} (PID: {worker.pid}) died! "
                            f"Exit code: {worker.exitcode}"
                        )
                        
                # Print summary
                if time.time() - last_summary_time >= 10.0:
                    self._print_health_summary()
                    last_summary_time = time.time()
                    
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted")
            
    def _print_health_summary(self):
        """Print health summary."""
        running = sum(1 for w in self.workers if w.is_alive())
        total_cameras = sum(
            r.get('active_cameras', 0) for r in self.last_health_reports.values()
        )
        
        self.logger.info(
            f"GStreamer Health: {running}/{len(self.workers)} workers, "
            f"{total_cameras} cameras"
        )
        
        # Log encoder info
        for wid, report in sorted(self.last_health_reports.items()):
            encoder = report.get('encoder', 'unknown')
            metrics = report.get('metrics', {})
            self.logger.debug(
                f"  Worker {wid}: encoder={encoder}, "
                f"frames={metrics.get('frames_encoded', 0)}, "
                f"errors={metrics.get('encoding_errors', 0)}"
            )
            
    def stop(self, timeout: float = 15.0):
        """Stop all workers."""
        self.logger.info("Stopping GStreamer workers...")
        
        self.stop_event.set()
        
        for i, worker in enumerate(self.workers):
            if worker.is_alive():
                self.logger.info(f"Waiting for GStreamer worker {i}...")
                worker.join(timeout=timeout)
                
                if worker.is_alive():
                    self.logger.warning(f"Terminating worker {i}")
                    worker.terminate()
                    worker.join(timeout=5.0)
                    
        self.logger.info("="*60)
        self.logger.info("GSTREAMER SHUTDOWN COMPLETE")
        self.logger.info("="*60)
        self._print_final_summary()
        
    def _print_final_summary(self):
        """Print final summary."""
        total = sum(len(c) for c in self.worker_camera_assignments.values())
        
        self.logger.info(f"Total cameras assigned: {total}")
        self.logger.info(f"Workers started: {len(self.workers)}")
        self.logger.info(f"Encoder: {self.gstreamer_encoder}, Codec: {self.gstreamer_codec}")
        
        normal = sum(1 for w in self.workers if w.exitcode == 0)
        errors = sum(1 for w in self.workers if w.exitcode and w.exitcode != 0)
        
        self.logger.info(f"Exit status: {normal} normal, {errors} errors")
        
    def run(self, duration: Optional[float] = None):
        """Start workers and monitor."""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.start()
            self.monitor(duration=duration)
            
        except Exception as exc:
            self.logger.error(f"Error in run loop: {exc}", exc_info=True)
            
        finally:
            self.stop()
            
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name}, shutting down...")
        self.stop_event.set()
        
    # ========================================================================
    # Dynamic Camera Management (same API as WorkerManager)
    # ========================================================================
    
    def add_camera(self, camera_config: Dict[str, Any]) -> bool:
        """Add a camera to least-loaded worker."""
        stream_key = camera_config.get('stream_key')
        
        if not stream_key:
            return False
            
        if stream_key in self.camera_to_worker:
            self.logger.warning(f"Camera {stream_key} already exists")
            return False
            
        target = self._find_least_loaded_worker()
        if target is None:
            self.logger.error("All workers at capacity")
            return False
            
        command = {
            'type': 'add_camera',
            'camera_config': camera_config,
            'timestamp': time.time()
        }
        
        try:
            self.command_queues[target].put(command, timeout=5.0)
            self.camera_to_worker[stream_key] = target
            self.worker_camera_count[target] += 1
            self.logger.info(f"Sent add_camera for {stream_key} to worker {target}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to add camera: {exc}")
            return False
            
    def remove_camera(self, stream_key: str) -> bool:
        """Remove a camera."""
        if stream_key not in self.camera_to_worker:
            return False
            
        worker_id = self.camera_to_worker[stream_key]
        
        command = {
            'type': 'remove_camera',
            'stream_key': stream_key,
            'timestamp': time.time()
        }
        
        try:
            self.command_queues[worker_id].put(command, timeout=5.0)
            del self.camera_to_worker[stream_key]
            self.worker_camera_count[worker_id] -= 1
            self.logger.info(f"Sent remove_camera for {stream_key}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to remove camera: {exc}")
            return False
            
    def update_camera(self, camera_config: Dict[str, Any]) -> bool:
        """Update a camera's configuration."""
        stream_key = camera_config.get('stream_key')
        
        if not stream_key:
            return False
            
        if stream_key not in self.camera_to_worker:
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
            return True
        except Exception as exc:
            self.logger.error(f"Failed to update camera: {exc}")
            return False
            
    def _find_least_loaded_worker(self) -> Optional[int]:
        """Find worker with least cameras."""
        available = []
        for wid, count in self.worker_camera_count.items():
            if count < self.max_cameras_per_worker and wid in self.command_queues:
                if wid < len(self.workers) and self.workers[wid].is_alive():
                    available.append((wid, count))
                    
        if not available:
            return None
            
        return min(available, key=lambda x: x[1])[0]
        
    def get_camera_assignments(self) -> Dict[str, int]:
        """Get camera-to-worker assignments."""
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
        """Get worker statistics."""
        # First, flush all pending health reports from the queue
        self._flush_health_queue()

        # Aggregate per-camera stats from all workers
        per_camera_stats = {}
        for worker_id, report in self.last_health_reports.items():
            worker_camera_stats = report.get('per_camera_stats', {})
            per_camera_stats.update(worker_camera_stats)

        return {
            'worker_type': 'gstreamer',
            'num_workers': len(self.workers),
            'running_workers': sum(1 for w in self.workers if w.is_alive()),
            'total_cameras': sum(self.worker_camera_count.values()),
            'camera_assignments': self.camera_to_worker.copy(),
            'worker_camera_counts': self.worker_camera_count.copy(),
            'encoder': self.gstreamer_encoder,
            'codec': self.gstreamer_codec,
            'gpu_id': self.gpu_id,
            'per_camera_stats': per_camera_stats,
            'health_reports': {
                wid: {
                    'status': r.get('status'),
                    'active_cameras': r.get('active_cameras', 0),
                    'encoder': r.get('encoder'),
                    'metrics': r.get('metrics', {}),
                }
                for wid, r in self.last_health_reports.items()
            }
        }
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

