"""Benchmark all 4 streaming modes with videoplayback.mp4.

This script tests and compares performance across all streaming modes:
- Mode 1: CameraStreamer (single-threaded OpenCV)
- Mode 2: WorkerManager (multi-process OpenCV)
- Mode 3: GStreamerCameraStreamer (single-threaded GStreamer)
- Mode 4: GStreamerWorkerManager (multi-process GStreamer)

Usage:
    python -m matrice_streaming.streaming_gateway.debug.test_videoplayback

Or run directly (from project root):
    python src/matrice_streaming/streaming_gateway/debug/test_videoplayback.py

With custom options:
    python src/matrice_streaming/streaming_gateway/debug/test_videoplayback.py --duration 60 --fps 30
"""
import sys
from pathlib import Path

# Add src to path for direct execution - must be before other imports
# Path: debug -> streaming_gateway -> matrice_streaming -> src
_script_dir = Path(__file__).resolve().parent
_src_dir = _script_dir.parent.parent.parent  # Goes to src/
_project_dir = _src_dir.parent  # Goes to py_streaming/
_common_src = _project_dir / "py_common" / "src"  # py_common/src for matrice_common

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if _common_src.exists() and str(_common_src) not in sys.path:
    sys.path.insert(0, str(_common_src))

import os
import time
import logging
import argparse
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def benchmark_mode(
    mode_name: str,
    gateway,
    duration_seconds: int = 30
) -> Dict[str, Any]:
    """Benchmark a single streaming mode.

    Args:
        mode_name: Name of the streaming mode
        gateway: Gateway instance to benchmark
        duration_seconds: How long to run the benchmark

    Returns:
        Dictionary with benchmark results
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking {mode_name}")
    print(f"{'='*60}")

    # Start streaming
    start_time = time.time()
    success = gateway.start_streaming(block=False)

    if not success:
        print(f"Failed to start {mode_name}")
        return {
            'mode': mode_name,
            'success': False,
            'error': 'Failed to start streaming',
        }

    # Run for specified duration
    print(f"Running for {duration_seconds} seconds...")
    time.sleep(duration_seconds)

    # Get statistics before stopping
    stats = gateway.get_statistics()

    # Stop streaming
    gateway.stop_streaming()

    elapsed = time.time() - start_time

    # Extract key metrics
    transmission_stats = stats.get('transmission_stats', {})
    total_frames = transmission_stats.get('total_frames_sent', 0)
    total_bytes = transmission_stats.get('total_bytes_sent', 0)

    avg_fps = total_frames / elapsed if elapsed > 0 else 0
    bandwidth_mbps = (total_bytes * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0

    result = {
        'mode': mode_name,
        'success': True,
        'runtime_seconds': elapsed,
        'total_frames': total_frames,
        'total_bytes': total_bytes,
        'avg_fps': avg_fps,
        'bandwidth_mbps': bandwidth_mbps,
        'cache_efficiency': stats.get('cache_efficiency', 0),
        'stats': stats,
    }

    print(f"\nResults for {mode_name}:")
    print(f"  Runtime: {elapsed:.1f}s")
    print(f"  Total frames: {total_frames:,}")
    print(f"  Avg FPS: {avg_fps:.2f}")
    print(f"  Bandwidth: {bandwidth_mbps:.2f} Mbps")

    if stats.get('cache_efficiency'):
        print(f"  Cache efficiency: {stats.get('cache_efficiency', 0):.1f}%")

    return result


def run_mode1_benchmark(video_path: str, fps: int, duration: int) -> Optional[Dict]:
    """Benchmark Mode 1: CameraStreamer (single-threaded OpenCV)."""
    try:
        from matrice_streaming.streaming_gateway.debug.debug_streaming_gateway import DebugStreamingGateway

        gateway = DebugStreamingGateway(
            video_paths=[video_path],
            fps=fps,
            video_codec="h264",
            loop_videos=True,
            use_workers=False,  # Single-threaded
            log_messages=False,
        )
        return benchmark_mode("Mode 1 (CameraStreamer)", gateway, duration)
    except Exception as e:
        logger.error(f"Mode 1 failed: {e}")
        return {'mode': 'Mode 1 (CameraStreamer)', 'success': False, 'error': str(e)}


def run_mode2_benchmark(video_path: str, fps: int, duration: int, num_workers: int = 2) -> Optional[Dict]:
    """Benchmark Mode 2: WorkerManager (multi-process OpenCV)."""
    try:
        from matrice_streaming.streaming_gateway.debug.debug_streaming_gateway import DebugStreamingGateway

        gateway = DebugStreamingGateway(
            video_paths=[video_path],
            fps=fps,
            video_codec="h264",
            loop_videos=True,
            use_workers=True,  # Multi-process
            num_workers=num_workers,
            log_messages=False,
        )
        return benchmark_mode(f"Mode 2 (WorkerManager, {num_workers} workers)", gateway, duration)
    except Exception as e:
        logger.error(f"Mode 2 failed: {e}")
        return {'mode': 'Mode 2 (WorkerManager)', 'success': False, 'error': str(e)}


def run_mode3_benchmark(video_path: str, fps: int, duration: int) -> Optional[Dict]:
    """Benchmark Mode 3: GStreamerCameraStreamer (single-threaded GStreamer)."""
    try:
        from matrice_streaming.streaming_gateway.debug.debug_gstreamer_gateway import DebugGStreamerGateway

        gateway = DebugGStreamerGateway(
            video_paths=[video_path],
            fps=fps,
            gstreamer_encoder="jpeg",
            jpeg_quality=85,
            loop_videos=True,
            use_workers=False,  # Single-threaded
            enable_frame_optimizer=True,
            log_messages=False,
        )
        return benchmark_mode("Mode 3 (GStreamer)", gateway, duration)
    except Exception as e:
        logger.error(f"Mode 3 failed: {e}")
        return {'mode': 'Mode 3 (GStreamer)', 'success': False, 'error': str(e)}


def run_mode4_benchmark(video_path: str, fps: int, duration: int, num_workers: int = 2) -> Optional[Dict]:
    """Benchmark Mode 4: GStreamerWorkerManager (multi-process GStreamer)."""
    try:
        from matrice_streaming.streaming_gateway.debug.debug_gstreamer_gateway import DebugGStreamerGateway

        gateway = DebugGStreamerGateway(
            video_paths=[video_path],
            fps=fps,
            gstreamer_encoder="jpeg",
            jpeg_quality=85,
            loop_videos=True,
            use_workers=True,  # Multi-process
            num_workers=num_workers,
            enable_frame_optimizer=True,
            log_messages=False,
        )
        return benchmark_mode(f"Mode 4 (GStreamer Workers, {num_workers} workers)", gateway, duration)
    except Exception as e:
        logger.error(f"Mode 4 failed: {e}")
        return {'mode': 'Mode 4 (GStreamer Workers)', 'success': False, 'error': str(e)}


def print_summary(results: List[Dict]):
    """Print benchmark comparison summary."""
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)

    # Filter successful results
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]

    if successful:
        print(f"\n{'Mode':<45} {'FPS':>10} {'Bandwidth':>15}")
        print("-"*70)

        for result in successful:
            print(f"{result['mode']:<45} {result['avg_fps']:>10.2f} {result['bandwidth_mbps']:>12.2f} Mbps")

        # Find best performers
        if len(successful) > 1:
            best_fps = max(successful, key=lambda r: r['avg_fps'])
            best_bandwidth = min(successful, key=lambda r: r['bandwidth_mbps'])

            print(f"\nBest FPS: {best_fps['mode']} ({best_fps['avg_fps']:.2f} fps)")
            print(f"Lowest Bandwidth: {best_bandwidth['mode']} ({best_bandwidth['bandwidth_mbps']:.2f} Mbps)")

    if failed:
        print("\nFailed modes:")
        for result in failed:
            print(f"  - {result['mode']}: {result.get('error', 'Unknown error')}")


def main():
    """Benchmark all 4 streaming modes."""
    parser = argparse.ArgumentParser(description="Benchmark all streaming modes")
    parser.add_argument("--video", type=str, default="videoplayback.mp4",
                       help="Video file to use for benchmarking")
    parser.add_argument("--duration", type=int, default=30,
                       help="Duration in seconds for each benchmark")
    parser.add_argument("--fps", type=int, default=30,
                       help="Target FPS")
    parser.add_argument("--workers", type=int, default=2,
                       help="Number of workers for multi-process modes")
    parser.add_argument("--modes", type=str, default="all",
                       help="Modes to test: all, 1, 2, 3, 4, or comma-separated (e.g., '1,3')")

    args = parser.parse_args()

    video_path = args.video

    if not Path(video_path).exists():
        print(f"Error: {video_path} not found")
        print(f"Current directory: {Path.cwd()}")
        return

    print("="*70)
    print("STREAMING MODE BENCHMARK")
    print("="*70)
    print(f"\nVideo: {video_path}")
    print(f"Duration: {args.duration}s per mode")
    print(f"Target FPS: {args.fps}")
    print(f"Workers: {args.workers}")

    results = []

    # Determine which modes to run
    if args.modes == "all":
        modes_to_run = [1, 2, 3, 4]
    else:
        modes_to_run = [int(m.strip()) for m in args.modes.split(',')]

    # Run benchmarks with delay between modes for resource cleanup
    if 1 in modes_to_run:
        print("\n" + "="*70)
        print("MODE 1: CameraStreamer (single-threaded OpenCV)")
        print("="*70)
        result = run_mode1_benchmark(video_path, args.fps, args.duration)
        if result:
            results.append(result)
        time.sleep(2)  # Allow cleanup

    if 2 in modes_to_run:
        print("\n" + "="*70)
        print("MODE 2: WorkerManager (multi-process OpenCV)")
        print("="*70)
        result = run_mode2_benchmark(video_path, args.fps, args.duration, args.workers)
        if result:
            results.append(result)
        time.sleep(2)  # Allow cleanup

    if 3 in modes_to_run:
        print("\n" + "="*70)
        print("MODE 3: GStreamerCameraStreamer (single-threaded GStreamer)")
        print("="*70)
        result = run_mode3_benchmark(video_path, args.fps, args.duration)
        if result:
            results.append(result)
        time.sleep(2)  # Allow GStreamer cleanup before Mode 4

    if 4 in modes_to_run:
        print("\n" + "="*70)
        print("MODE 4: GStreamerWorkerManager (multi-process GStreamer)")
        print("="*70)
        result = run_mode4_benchmark(video_path, args.fps, args.duration, args.workers)
        if result:
            results.append(result)

    # Print summary
    print_summary(results)

    print("\n" + "="*70)
    print("Benchmark complete!")
    print("="*70)


if __name__ == "__main__":
    main()
