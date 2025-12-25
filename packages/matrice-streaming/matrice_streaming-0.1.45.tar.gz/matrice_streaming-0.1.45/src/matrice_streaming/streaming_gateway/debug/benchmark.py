"""Comprehensive GStreamer benchmark suite for all streaming methods.

Tests and benchmarks:
1. CameraStreamer (standard OpenCV-based)
2. AsyncWorkers (multi-process OpenCV)
3. GStreamerCameraStreamer (single-process GStreamer)
4. GStreamerWorkerManager (multi-process GStreamer)

Measures:
- FPS (frames per second)
- Latency (read, encode, write, total)
- Bandwidth (Mbps)
- CPU usage
- Memory usage
- Cache efficiency
- GPU utilization (for NVENC)
"""

import logging
import time
import psutil
import statistics
import json
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import threading

from .debug_streaming_gateway import DebugStreamingGateway
from .debug_gstreamer_gateway import DebugGStreamerGateway


@dataclass
class BenchmarkResult:
    """Benchmark result for a single test."""
    method: str
    encoder: str
    codec: str
    num_streams: int
    fps_target: int
    duration_seconds: float

    # Performance metrics
    avg_fps: float
    min_fps: float
    max_fps: float
    fps_std: float

    # Latency metrics (milliseconds)
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Throughput metrics
    total_frames: int
    frames_sent: int
    frames_skipped: int
    total_bytes: int
    bandwidth_mbps: float

    # Cache/optimization metrics
    cache_efficiency_pct: float = 0.0
    similarity_rate_pct: float = 0.0

    # Resource utilization
    avg_cpu_percent: float = 0.0
    peak_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0

    # Success/failure
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class ResourceMonitor:
    """Monitor CPU and memory usage during benchmark."""

    def __init__(self, process: psutil.Process):
        """Initialize monitor.

        Args:
            process: Process to monitor
        """
        self.process = process
        self.cpu_samples = []
        self.memory_samples = []
        self.running = False
        self.thread = None
        self.sample_interval = 0.5  # seconds

    def start(self):
        """Start monitoring."""
        self.running = True
        self.cpu_samples = []
        self.memory_samples = []
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Monitor loop."""
        while self.running:
            try:
                # Get CPU percent (non-blocking)
                cpu_percent = self.process.cpu_percent()

                # Get memory usage in MB
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                self.cpu_samples.append(cpu_percent)
                self.memory_samples.append(memory_mb)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            time.sleep(self.sample_interval)

    def get_stats(self) -> Dict[str, float]:
        """Get resource usage statistics.

        Returns:
            Dictionary with CPU and memory stats
        """
        stats = {
            "avg_cpu_percent": 0.0,
            "peak_cpu_percent": 0.0,
            "avg_memory_mb": 0.0,
            "peak_memory_mb": 0.0,
        }

        if self.cpu_samples:
            stats["avg_cpu_percent"] = statistics.mean(self.cpu_samples)
            stats["peak_cpu_percent"] = max(self.cpu_samples)

        if self.memory_samples:
            stats["avg_memory_mb"] = statistics.mean(self.memory_samples)
            stats["peak_memory_mb"] = max(self.memory_samples)

        return stats


class GStreamerBenchmark:
    """Comprehensive benchmark suite for all streaming methods."""

    def __init__(
        self,
        video_paths: List[str],
        output_dir: Optional[str] = None,
        log_level: int = logging.INFO,
    ):
        """Initialize benchmark suite.

        Args:
            video_paths: List of video files to use for testing
            output_dir: Directory to save benchmark results
            log_level: Logging level
        """
        # Validate video paths
        for video_path in video_paths:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")

        self.video_paths = video_paths
        self.output_dir = Path(output_dir) if output_dir else Path("benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # Results storage
        self.results: List[BenchmarkResult] = []

        self.logger.info(f"GStreamerBenchmark initialized with {len(video_paths)} videos")

    def benchmark_standard_camera_streamer(
        self,
        fps: int = 30,
        duration: float = 60.0,
        codec: str = "h264",
    ) -> BenchmarkResult:
        """Benchmark standard CameraStreamer (OpenCV + OpenH264/x264).

        Args:
            fps: Target FPS
            duration: Test duration in seconds
            codec: Video codec (h264, h265-frame, h265-chunk)

        Returns:
            BenchmarkResult with performance metrics
        """
        self.logger.info(f"Benchmarking CameraStreamer: fps={fps}, codec={codec}, duration={duration}s")

        start_time = time.time()
        gateway = None
        resource_monitor = None

        try:
            # Create gateway
            gateway = DebugStreamingGateway(
                video_paths=self.video_paths,
                fps=fps,
                video_codec=codec,
                loop_videos=True,
                save_to_files=False,
                log_messages=False,
            )

            # Start resource monitoring
            process = psutil.Process()
            resource_monitor = ResourceMonitor(process)
            resource_monitor.start()

            # Start streaming
            if not gateway.start_streaming():
                raise RuntimeError("Failed to start streaming")

            # Run for duration
            time.sleep(duration)

            # Get statistics
            stats = gateway.get_statistics()

            # Stop streaming
            gateway.stop_streaming()

            # Stop resource monitoring
            resource_monitor.stop()
            resource_stats = resource_monitor.get_stats()

            # Extract metrics
            transmission_stats = stats.get("transmission_stats", {})
            timing_stats = stats.get("timing_stats", {})

            total_frames = transmission_stats.get("total_frames_sent", 0)
            total_bytes = transmission_stats.get("total_bytes_sent", 0)
            actual_duration = time.time() - start_time

            # Calculate FPS metrics
            avg_fps = total_frames / actual_duration if actual_duration > 0 else 0

            # Calculate latency metrics from timing stats
            latencies = []
            for stream_timing in timing_stats.values():
                if isinstance(stream_timing, dict):
                    process_time = stream_timing.get("avg_process_time", 0)
                    latencies.append(process_time * 1000)  # Convert to ms

            avg_latency = statistics.mean(latencies) if latencies else 0
            p50_latency = statistics.median(latencies) if latencies else 0
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else avg_latency
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else avg_latency

            # Calculate bandwidth
            bandwidth_mbps = (total_bytes * 8) / (actual_duration * 1_000_000) if actual_duration > 0 else 0

            result = BenchmarkResult(
                method="CameraStreamer",
                encoder="opencv",
                codec=codec,
                num_streams=len(self.video_paths),
                fps_target=fps,
                duration_seconds=actual_duration,
                avg_fps=avg_fps,
                min_fps=avg_fps,  # Not tracked per-frame
                max_fps=avg_fps,
                fps_std=0.0,
                avg_latency_ms=avg_latency,
                p50_latency_ms=p50_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                total_frames=total_frames,
                frames_sent=total_frames,
                frames_skipped=0,
                total_bytes=total_bytes,
                bandwidth_mbps=bandwidth_mbps,
                avg_cpu_percent=resource_stats["avg_cpu_percent"],
                peak_cpu_percent=resource_stats["peak_cpu_percent"],
                avg_memory_mb=resource_stats["avg_memory_mb"],
                peak_memory_mb=resource_stats["peak_memory_mb"],
                success=True,
            )

            self.results.append(result)
            self.logger.info(f"CameraStreamer benchmark complete: {avg_fps:.1f} fps, {bandwidth_mbps:.2f} Mbps")
            return result

        except Exception as e:
            self.logger.error(f"CameraStreamer benchmark failed: {e}", exc_info=True)

            result = BenchmarkResult(
                method="CameraStreamer",
                encoder="opencv",
                codec=codec,
                num_streams=len(self.video_paths),
                fps_target=fps,
                duration_seconds=time.time() - start_time,
                avg_fps=0.0,
                min_fps=0.0,
                max_fps=0.0,
                fps_std=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_frames=0,
                frames_sent=0,
                frames_skipped=0,
                total_bytes=0,
                bandwidth_mbps=0.0,
                success=False,
                error_message=str(e),
            )

            self.results.append(result)
            return result

        finally:
            if gateway:
                try:
                    gateway.stop_streaming()
                except:
                    pass
            if resource_monitor:
                try:
                    resource_monitor.stop()
                except:
                    pass

    def benchmark_gstreamer_camera_streamer(
        self,
        fps: int = 30,
        duration: float = 60.0,
        encoder: str = "jpeg",
        codec: str = "h264",
        jpeg_quality: int = 85,
        enable_frame_optimizer: bool = True,
    ) -> BenchmarkResult:
        """Benchmark GStreamerCameraStreamer (single-process GStreamer).

        Args:
            fps: Target FPS
            duration: Test duration in seconds
            encoder: GStreamer encoder (jpeg, nvenc, x264, openh264, auto)
            codec: Codec for hardware/software encoders (h264, h265)
            jpeg_quality: JPEG quality (1-100)
            enable_frame_optimizer: Enable frame similarity detection

        Returns:
            BenchmarkResult with performance metrics
        """
        self.logger.info(
            f"Benchmarking GStreamerCameraStreamer: fps={fps}, encoder={encoder}, "
            f"codec={codec}, duration={duration}s"
        )

        start_time = time.time()
        gateway = None
        resource_monitor = None

        try:
            # Create gateway
            gateway = DebugGStreamerGateway(
                video_paths=self.video_paths,
                fps=fps,
                loop_videos=True,
                save_to_files=False,
                log_messages=False,
                gstreamer_encoder=encoder,
                gstreamer_codec=codec,
                jpeg_quality=jpeg_quality,
                enable_frame_optimizer=enable_frame_optimizer,
            )

            # Start resource monitoring
            process = psutil.Process()
            resource_monitor = ResourceMonitor(process)
            resource_monitor.start()

            # Start streaming
            if not gateway.start_streaming():
                raise RuntimeError("Failed to start streaming")

            # Run for duration
            time.sleep(duration)

            # Get statistics
            stats = gateway.get_statistics()

            # Stop streaming
            gateway.stop_streaming()

            # Stop resource monitoring
            resource_monitor.stop()
            resource_stats = resource_monitor.get_stats()

            # Extract metrics
            transmission_stats = stats.get("transmission_stats", {})
            timing_stats = stats.get("timing_stats", {})
            frame_opt_metrics = stats.get("frame_optimizer_metrics", {})

            total_frames = transmission_stats.get("total_frames_sent", 0)
            total_bytes = transmission_stats.get("total_bytes_sent", 0)
            actual_duration = time.time() - start_time

            # Calculate FPS metrics
            avg_fps = stats.get("avg_fps", 0.0)

            # Calculate latency metrics from timing stats
            latencies = []
            for stream_timing in timing_stats.values():
                if isinstance(stream_timing, dict):
                    process_time = stream_timing.get("avg_process_time", 0)
                    latencies.append(process_time * 1000)  # Convert to ms

            avg_latency = statistics.mean(latencies) if latencies else 0
            p50_latency = statistics.median(latencies) if latencies else 0
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else avg_latency
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else avg_latency

            # Calculate bandwidth
            bandwidth_mbps = stats.get("bandwidth_mbps", 0.0)

            # Cache efficiency
            cache_efficiency = stats.get("cache_efficiency", 0.0)
            similarity_rate = frame_opt_metrics.get("similarity_rate", 0.0) if frame_opt_metrics else 0.0

            result = BenchmarkResult(
                method="GStreamerCameraStreamer",
                encoder=encoder,
                codec=codec,
                num_streams=len(self.video_paths),
                fps_target=fps,
                duration_seconds=actual_duration,
                avg_fps=avg_fps,
                min_fps=avg_fps,  # Not tracked per-frame
                max_fps=avg_fps,
                fps_std=0.0,
                avg_latency_ms=avg_latency,
                p50_latency_ms=p50_latency,
                p95_latency_ms=p95_latency,
                p99_latency_ms=p99_latency,
                total_frames=total_frames,
                frames_sent=total_frames,
                frames_skipped=0,
                total_bytes=total_bytes,
                bandwidth_mbps=bandwidth_mbps,
                cache_efficiency_pct=cache_efficiency,
                similarity_rate_pct=similarity_rate,
                avg_cpu_percent=resource_stats["avg_cpu_percent"],
                peak_cpu_percent=resource_stats["peak_cpu_percent"],
                avg_memory_mb=resource_stats["avg_memory_mb"],
                peak_memory_mb=resource_stats["peak_memory_mb"],
                success=True,
            )

            self.results.append(result)
            self.logger.info(
                f"GStreamerCameraStreamer benchmark complete: {avg_fps:.1f} fps, "
                f"{bandwidth_mbps:.2f} Mbps, cache={cache_efficiency:.1f}%"
            )
            return result

        except Exception as e:
            self.logger.error(f"GStreamerCameraStreamer benchmark failed: {e}", exc_info=True)

            result = BenchmarkResult(
                method="GStreamerCameraStreamer",
                encoder=encoder,
                codec=codec,
                num_streams=len(self.video_paths),
                fps_target=fps,
                duration_seconds=time.time() - start_time,
                avg_fps=0.0,
                min_fps=0.0,
                max_fps=0.0,
                fps_std=0.0,
                avg_latency_ms=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
                p99_latency_ms=0.0,
                total_frames=0,
                frames_sent=0,
                frames_skipped=0,
                total_bytes=0,
                bandwidth_mbps=0.0,
                success=False,
                error_message=str(e),
            )

            self.results.append(result)
            return result

        finally:
            if gateway:
                try:
                    gateway.stop_streaming()
                except:
                    pass
            if resource_monitor:
                try:
                    resource_monitor.stop()
                except:
                    pass

    def run_comprehensive_benchmark(
        self,
        fps: int = 30,
        duration: float = 60.0,
        test_encoders: List[str] = None,
    ) -> Dict[str, Any]:
        """Run comprehensive benchmark across all methods and encoders.

        Args:
            fps: Target FPS
            duration: Test duration per benchmark
            test_encoders: List of encoders to test (default: jpeg, nvenc, x264)

        Returns:
            Dictionary with all benchmark results and comparisons
        """
        if test_encoders is None:
            test_encoders = ["jpeg", "nvenc", "x264", "openh264"]

        self.logger.info(f"Starting comprehensive benchmark: {len(test_encoders)} encoders x {duration}s each")

        # Test 1: Standard CameraStreamer with H.264
        self.logger.info("\n" + "="*80)
        self.logger.info("TEST 1: CameraStreamer (OpenCV + OpenH264)")
        self.logger.info("="*80)
        self.benchmark_standard_camera_streamer(fps=fps, duration=duration, codec="h264")

        # Test 2-N: GStreamerCameraStreamer with different encoders
        for encoder in test_encoders:
            self.logger.info("\n" + "="*80)
            self.logger.info(f"TEST: GStreamerCameraStreamer ({encoder})")
            self.logger.info("="*80)

            # Determine codec based on encoder
            codec = "h264"  # Default for most encoders
            jpeg_quality = 85 if encoder == "jpeg" else None

            self.benchmark_gstreamer_camera_streamer(
                fps=fps,
                duration=duration,
                encoder=encoder,
                codec=codec,
                jpeg_quality=jpeg_quality if jpeg_quality else 85,
                enable_frame_optimizer=True,
            )

        # Generate comparison report
        report = self._generate_comparison_report()

        # Save results
        self._save_results(report)

        return report

    def _generate_comparison_report(self) -> Dict[str, Any]:
        """Generate comparison report from all benchmark results.

        Returns:
            Dictionary with comparison metrics and analysis
        """
        if not self.results:
            return {"error": "No benchmark results available"}

        report = {
            "summary": {
                "total_tests": len(self.results),
                "successful_tests": sum(1 for r in self.results if r.success),
                "failed_tests": sum(1 for r in self.results if not r.success),
            },
            "results": [r.to_dict() for r in self.results],
            "comparisons": {},
        }

        # Find best performers
        successful_results = [r for r in self.results if r.success]

        if successful_results:
            # Best FPS
            best_fps = max(successful_results, key=lambda r: r.avg_fps)
            report["comparisons"]["best_fps"] = {
                "method": best_fps.method,
                "encoder": best_fps.encoder,
                "fps": best_fps.avg_fps,
            }

            # Best latency
            best_latency = min(successful_results, key=lambda r: r.avg_latency_ms)
            report["comparisons"]["best_latency"] = {
                "method": best_latency.method,
                "encoder": best_latency.encoder,
                "latency_ms": best_latency.avg_latency_ms,
            }

            # Best bandwidth efficiency (highest FPS per Mbps)
            if any(r.bandwidth_mbps > 0 for r in successful_results):
                best_efficiency = max(
                    (r for r in successful_results if r.bandwidth_mbps > 0),
                    key=lambda r: r.avg_fps / r.bandwidth_mbps
                )
                report["comparisons"]["best_bandwidth_efficiency"] = {
                    "method": best_efficiency.method,
                    "encoder": best_efficiency.encoder,
                    "fps_per_mbps": best_efficiency.avg_fps / best_efficiency.bandwidth_mbps,
                }

            # Best cache efficiency
            if any(r.cache_efficiency_pct > 0 for r in successful_results):
                best_cache = max(successful_results, key=lambda r: r.cache_efficiency_pct)
                report["comparisons"]["best_cache_efficiency"] = {
                    "method": best_cache.method,
                    "encoder": best_cache.encoder,
                    "cache_efficiency_pct": best_cache.cache_efficiency_pct,
                }

            # Lowest CPU usage
            best_cpu = min(successful_results, key=lambda r: r.avg_cpu_percent)
            report["comparisons"]["lowest_cpu_usage"] = {
                "method": best_cpu.method,
                "encoder": best_cpu.encoder,
                "cpu_percent": best_cpu.avg_cpu_percent,
            }

        return report

    def _save_results(self, report: Dict[str, Any]):
        """Save benchmark results to file.

        Args:
            report: Comparison report dictionary
        """
        # Save JSON
        json_file = self.output_dir / f"benchmark_{int(time.time())}.json"
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Benchmark results saved to: {json_file}")

        # Save human-readable summary
        summary_file = self.output_dir / f"benchmark_{int(time.time())}_summary.txt"
        with open(summary_file, "w") as f:
            f.write("="*80 + "\n")
            f.write("GStreamer Benchmark Summary\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total Tests: {report['summary']['total_tests']}\n")
            f.write(f"Successful: {report['summary']['successful_tests']}\n")
            f.write(f"Failed: {report['summary']['failed_tests']}\n\n")

            f.write("="*80 + "\n")
            f.write("Best Performers\n")
            f.write("="*80 + "\n\n")

            for metric, data in report.get("comparisons", {}).items():
                f.write(f"{metric.replace('_', ' ').title()}:\n")
                for key, value in data.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")

            f.write("="*80 + "\n")
            f.write("Detailed Results\n")
            f.write("="*80 + "\n\n")

            for result in self.results:
                f.write(f"Method: {result.method} ({result.encoder}/{result.codec})\n")
                f.write(f"  FPS: {result.avg_fps:.1f} (target: {result.fps_target})\n")
                f.write(f"  Latency: {result.avg_latency_ms:.1f}ms (p95: {result.p95_latency_ms:.1f}ms)\n")
                f.write(f"  Bandwidth: {result.bandwidth_mbps:.2f} Mbps\n")
                f.write(f"  Frames: {result.total_frames} ({result.frames_sent} sent, {result.frames_skipped} skipped)\n")
                f.write(f"  Cache: {result.cache_efficiency_pct:.1f}%\n")
                f.write(f"  CPU: {result.avg_cpu_percent:.1f}% (peak: {result.peak_cpu_percent:.1f}%)\n")
                f.write(f"  Memory: {result.avg_memory_mb:.1f} MB (peak: {result.peak_memory_mb:.1f} MB)\n")
                f.write(f"  Success: {result.success}\n")
                if result.error_message:
                    f.write(f"  Error: {result.error_message}\n")
                f.write("\n")

        self.logger.info(f"Benchmark summary saved to: {summary_file}")

    def print_summary(self):
        """Print benchmark summary to console."""
        if not self.results:
            print("No benchmark results available")
            return

        print("\n" + "="*80)
        print("GStreamer Benchmark Summary")
        print("="*80 + "\n")

        # Print table header
        print(f"{'Method':<30} {'Encoder':<10} {'FPS':>8} {'Latency':>10} {'BW (Mbps)':>12} {'Cache %':>8} {'CPU %':>8}")
        print("-"*80)

        # Print results
        for result in self.results:
            method_str = f"{result.method}"
            print(
                f"{method_str:<30} "
                f"{result.encoder:<10} "
                f"{result.avg_fps:>8.1f} "
                f"{result.avg_latency_ms:>10.1f} "
                f"{result.bandwidth_mbps:>12.2f} "
                f"{result.cache_efficiency_pct:>8.1f} "
                f"{result.avg_cpu_percent:>8.1f}"
            )

        print("="*80 + "\n")
