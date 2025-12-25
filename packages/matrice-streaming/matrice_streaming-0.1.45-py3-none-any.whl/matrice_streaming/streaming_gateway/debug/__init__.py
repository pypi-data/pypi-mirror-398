"""Debug module for testing streaming gateway without external dependencies.

This module provides mock implementations for testing the streaming pipeline
without requiring Kafka, Redis, or API connectivity.

Example usage:
    from matrice_streaming.streaming_gateway.debug import DebugStreamingGateway
    
    # Create debug gateway with local video files
    gateway = DebugStreamingGateway(
        video_paths=["video1.mp4", "video2.mp4"],
        fps=10,
        video_codec="h265-frame",
        save_to_files=True,
        output_dir="./debug_output"
    )
    
    # Start streaming
    gateway.start_streaming()
    
    # Check stats
    import time
    time.sleep(30)
    print(gateway.get_statistics())
    
    # Stop
    gateway.stop_streaming()
"""

from .debug_streaming_gateway import DebugStreamingGateway, DebugStreamingAction
from .debug_stream_backend import DebugStreamBackend
from .debug_utils import (
    MockSession,
    MockRPC,
    create_debug_input_streams,
    create_camera_configs_from_streams,
)

# GStreamer debug classes (optional import)
try:
    from .debug_gstreamer_gateway import DebugGStreamerGateway
    from .gstreamer_benchmark import GStreamerBenchmark, BenchmarkResult
    _GSTREAMER_DEBUG_AVAILABLE = True
except (ImportError, ValueError):
    # ImportError: gi module not available
    # ValueError: gi.require_version fails when GStreamer not installed
    _GSTREAMER_DEBUG_AVAILABLE = False

__all__ = [
    # Main debug gateway classes (support both single-threaded and worker modes)
    "DebugStreamingGateway",  # Modes 1 & 2 (CameraStreamer / WorkerManager)
    "DebugStreamingAction",
    # Backend and utilities
    "DebugStreamBackend",
    "MockSession",
    "MockRPC",
    "create_debug_input_streams",
    "create_camera_configs_from_streams",
]

if _GSTREAMER_DEBUG_AVAILABLE:
    __all__.extend([
        "DebugGStreamerGateway",  # Modes 3 & 4 (GStreamerCameraStreamer / GStreamerWorkerManager)
        "GStreamerBenchmark",
        "BenchmarkResult",
    ])

