from .camera_streamer import CameraStreamer
from .worker_manager import WorkerManager
from .async_camera_worker import AsyncCameraWorker

# GStreamer components (optional - graceful import)
try:
    from .gstreamer_camera_streamer import (
        GStreamerCameraStreamer,
        GStreamerConfig,
        GStreamerPipeline,
        is_gstreamer_available,
    )
    from .gstreamer_worker import (
        GStreamerAsyncWorker,
        run_gstreamer_worker,
    )
    from .gstreamer_worker_manager import GStreamerWorkerManager

    GSTREAMER_AVAILABLE = is_gstreamer_available()
except (ImportError, ValueError):
    # ImportError: gi module not available
    # ValueError: gi.require_version fails when GStreamer not installed
    GSTREAMER_AVAILABLE = False
    GStreamerCameraStreamer = None
    GStreamerConfig = None
    GStreamerPipeline = None
    GStreamerAsyncWorker = None
    GStreamerWorkerManager = None
    
    def is_gstreamer_available():
        return False

__all__ = [
    # Original components
    "CameraStreamer",
    "WorkerManager", 
    "AsyncCameraWorker",
    # GStreamer components
    "GStreamerCameraStreamer",
    "GStreamerConfig",
    "GStreamerPipeline",
    "GStreamerAsyncWorker",
    "GStreamerWorkerManager",
    "is_gstreamer_available",
    "GSTREAMER_AVAILABLE",
]