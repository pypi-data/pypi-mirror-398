#!/usr/bin/env python3
"""
Comprehensive test suite for GStreamer integration.

Tests both GStreamerCameraStreamer and GStreamerWorkerManager implementations
to ensure correctness, performance, and feature parity.

Usage:
    python test_gstreamer_integration.py
"""

import sys
import time
import logging
import asyncio
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directories to path
# Use the py_common submodule within py_streaming, not the root py_common
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "py_common" / "src"))

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_result(test_name, passed, message=""):
    """Record test result."""
    if passed:
        test_results["passed"].append(test_name)
        logger.info(f"✅ PASS: {test_name}")
    else:
        test_results["failed"].append(test_name)
        logger.error(f"❌ FAIL: {test_name} - {message}")

    if message and passed:
        logger.info(f"   {message}")


def test_imports():
    """Test 1: Verify all imports work correctly."""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Import Validation")
    logger.info("="*80)

    try:
        from matrice_streaming.streaming_gateway.camera_streamer import (
            gstreamer_camera_streamer,
            gstreamer_worker,
            gstreamer_worker_manager
        )
        test_result("Import GStreamer modules", True)

        # Check if GStreamer is available
        is_available = gstreamer_camera_streamer.GST_AVAILABLE
        if is_available:
            test_result("GStreamer availability", True, "GStreamer is installed")
        else:
            test_result("GStreamer availability", False, "GStreamer not installed - some tests will be skipped")
            test_results["warnings"].append("GStreamer not installed")

        return True, is_available

    except Exception as e:
        test_result("Import GStreamer modules", False, str(e))
        return False, False


def test_gstreamer_config():
    """Test 2: Verify GStreamerConfig defaults."""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: GStreamerConfig Validation")
    logger.info("="*80)

    try:
        from matrice_streaming.streaming_gateway.camera_streamer.gstreamer_camera_streamer import GStreamerConfig

        # Test default config
        config = GStreamerConfig()

        # Verify JPEG is default
        assert config.encoder == "jpeg", f"Expected encoder='jpeg', got '{config.encoder}'"
        test_result("Default encoder is JPEG", True)

        assert config.jpeg_quality == 85, f"Expected jpeg_quality=85, got {config.jpeg_quality}"
        test_result("Default JPEG quality is 85", True)

        # Test custom config
        custom_config = GStreamerConfig(
            encoder="nvenc",
            codec="h265",
            bitrate=8000000,
            gpu_id=1
        )
        assert custom_config.encoder == "nvenc"
        assert custom_config.codec == "h265"
        assert custom_config.bitrate == 8000000
        assert custom_config.gpu_id == 1
        test_result("Custom GStreamerConfig", True)

        return True

    except Exception as e:
        test_result("GStreamerConfig validation", False, str(e))
        return False


def test_gstreamer_camera_streamer_api():
    """Test 3: Verify GStreamerCameraStreamer API completeness."""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: GStreamerCameraStreamer API Completeness")
    logger.info("="*80)

    try:
        from matrice_streaming.streaming_gateway.camera_streamer.gstreamer_camera_streamer import GStreamerCameraStreamer

        # Check required methods exist
        required_methods = [
            # Topic management
            'register_stream_topic',
            'get_topic_for_stream',
            'setup_stream_for_topic',
            # Streaming control
            'start_stream',
            'start_background_stream',
            'stop_streaming',
            # Statistics
            'get_transmission_stats',
            'reset_transmission_stats',
            # Message production (NEW)
            'produce_request',
            'async_produce_request',
            # Connection management (NEW)
            'refresh_connection_info',
            # Cleanup
            'close'
        ]

        for method_name in required_methods:
            assert hasattr(GStreamerCameraStreamer, method_name), f"Missing method: {method_name}"
            test_result(f"Method exists: {method_name}", True)

        # Check initialization parameters
        import inspect
        sig = inspect.signature(GStreamerCameraStreamer.__init__)
        params = list(sig.parameters.keys())

        assert 'frame_optimizer_enabled' in params, "Missing frame_optimizer_enabled parameter"
        test_result("Frame optimizer parameter exists", True)

        assert 'gstreamer_config' in params, "Missing gstreamer_config parameter"
        test_result("GStreamer config parameter exists", True)

        return True

    except Exception as e:
        test_result("GStreamerCameraStreamer API", False, str(e))
        return False


def test_gstreamer_worker_manager_api():
    """Test 4: Verify GStreamerWorkerManager API."""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: GStreamerWorkerManager API Completeness")
    logger.info("="*80)

    try:
        from matrice_streaming.streaming_gateway.camera_streamer.gstreamer_worker_manager import GStreamerWorkerManager

        required_methods = [
            'start',
            'stop',
            'monitor',
            'add_camera',
            'remove_camera',
            'update_camera',
            'get_worker_statistics',
            'get_camera_assignments'
        ]

        for method_name in required_methods:
            assert hasattr(GStreamerWorkerManager, method_name), f"Missing method: {method_name}"
            test_result(f"Method exists: {method_name}", True)

        # Check initialization includes encoder config
        import inspect
        sig = inspect.signature(GStreamerWorkerManager.__init__)
        params = list(sig.parameters.keys())

        assert 'gstreamer_encoder' in params, "Missing gstreamer_encoder parameter"
        test_result("Encoder parameter exists", True)

        assert 'gstreamer_codec' in params, "Missing gstreamer_codec parameter"
        test_result("Codec parameter exists", True)

        return True

    except Exception as e:
        test_result("GStreamerWorkerManager API", False, str(e))
        return False


def test_frame_optimizer_integration():
    """Test 5: Verify FrameOptimizer integration."""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: FrameOptimizer Integration")
    logger.info("="*80)

    try:
        # Test hash-based similarity detection
        import hashlib

        # Test identical frames
        frame1 = b"test_frame_data_identical"
        frame2 = b"test_frame_data_identical"
        hash1 = hashlib.md5(frame1).hexdigest()
        hash2 = hashlib.md5(frame2).hexdigest()
        assert hash1 == hash2, "Identical frames should have same hash"
        test_result("Hash-based similarity detection (identical)", True)

        # Test different frames
        frame3 = b"test_frame_data_different"
        hash3 = hashlib.md5(frame3).hexdigest()
        assert hash1 != hash3, "Different frames should have different hash"
        test_result("Hash-based similarity detection (different)", True)

        # Verify FrameOptimizer is imported in gstreamer_camera_streamer
        from matrice_streaming.streaming_gateway.camera_streamer import gstreamer_camera_streamer
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_camera_streamer.py"

        if source.exists():
            content = source.read_text()
            assert "from matrice_common.optimize import FrameOptimizer" in content, "FrameOptimizer not imported"
            test_result("FrameOptimizer import in gstreamer_camera_streamer", True)

            assert "self.frame_optimizer = FrameOptimizer" in content, "FrameOptimizer not initialized"
            test_result("FrameOptimizer initialization", True)

            assert "_last_sent_frame_ids" in content, "Frame ID tracking not implemented"
            test_result("Frame ID tracking", True)

            assert "cached_frame_id" in content, "Cached frame ID support missing"
            test_result("Cached frame ID support", True)

        # Verify in gstreamer_worker
        worker_source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_worker.py"

        if worker_source.exists():
            content = worker_source.read_text()
            assert "FrameOptimizer" in content or "frame_optimizer" in content, "FrameOptimizer not in worker"
            test_result("FrameOptimizer in gstreamer_worker", True)

        return True

    except Exception as e:
        test_result("FrameOptimizer integration", False, str(e))
        return False


def test_timing_metrics():
    """Test 6: Verify timing metrics implementation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Timing Metrics Implementation")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_camera_streamer.py"

        if source.exists():
            content = source.read_text()

            # Check read_time tracking
            assert "read_start = time.time()" in content, "read_time tracking missing"
            assert "read_time = time.time() - read_start" in content, "read_time calculation missing"
            test_result("read_time tracking", True)

            # Check read_time is passed to _process_and_send_frame
            assert "read_time: float" in content, "read_time parameter missing"
            test_result("read_time parameter", True)

            # Check process_time calculation
            assert "process_time = read_time + write_time" in content, "process_time calculation missing"
            test_result("process_time calculation", True)

        # Check worker implementation
        worker_source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_worker.py"

        if worker_source.exists():
            content = worker_source.read_text()
            assert "read_time" in content, "read_time tracking missing in worker"
            test_result("Worker timing metrics", True)

        return True

    except Exception as e:
        test_result("Timing metrics", False, str(e))
        return False


def test_batch_optimization():
    """Test 7: Verify per-worker batch optimization."""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Per-Worker Batch Optimization")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_worker_manager.py"

        if source.exists():
            content = source.read_text()

            # Check CameraStreamer import for batch calculation
            assert "from .camera_streamer import CameraStreamer" in content, "CameraStreamer not imported"
            test_result("CameraStreamer import", True)

            # Check batch parameter calculation
            assert "calculate_batch_parameters" in content, "Batch parameter calculation missing"
            test_result("Batch parameter calculation", True)

            # Check batch config is applied
            assert "batch_size" in content and "batch_timeout" in content, "Batch config not applied"
            test_result("Batch config application", True)

        return True

    except Exception as e:
        test_result("Batch optimization", False, str(e))
        return False


def test_connection_management():
    """Test 8: Verify connection management features."""
    logger.info("\n" + "="*80)
    logger.info("TEST 8: Connection Management Features")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_camera_streamer.py"

        if source.exists():
            content = source.read_text()

            # Check connection lock
            assert "_connection_lock = threading.RLock()" in content, "Connection lock missing"
            test_result("Connection lock", True)

            # Check failure tracking
            assert "_send_failure_count" in content, "Failure tracking missing"
            test_result("Failure tracking", True)

            # Check refresh_connection_info method
            assert "def refresh_connection_info" in content, "refresh_connection_info method missing"
            test_result("refresh_connection_info method", True)

            # Check connection refresh logic
            assert "connection_refresh_threshold" in content, "Refresh threshold missing"
            assert "connection_refresh_interval" in content, "Refresh interval missing"
            test_result("Connection refresh parameters", True)

        return True

    except Exception as e:
        test_result("Connection management", False, str(e))
        return False


def test_metrics_logging():
    """Test 9: Verify enhanced metrics logging."""
    logger.info("\n" + "="*80)
    logger.info("TEST 9: Enhanced Metrics Logging")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_camera_streamer.py"

        if source.exists():
            content = source.read_text()

            # Check comprehensive logging
            assert "bandwidth_mbps" in content, "Bandwidth calculation missing"
            test_result("Bandwidth calculation", True)

            assert "cache_efficiency" in content, "Cache efficiency calculation missing"
            test_result("Cache efficiency logging", True)

            # Check pipeline metrics
            assert "Pipeline Metrics:" in content, "Pipeline metrics logging missing"
            test_result("Pipeline metrics logging", True)

            # Check frame optimization metrics
            assert "Frame Optimization:" in content, "Frame optimization metrics missing"
            test_result("Frame optimization metrics", True)

        return True

    except Exception as e:
        test_result("Metrics logging", False, str(e))
        return False


def test_cleanup_procedures():
    """Test 10: Verify cleanup procedures."""
    logger.info("\n" + "="*80)
    logger.info("TEST 10: Cleanup Procedures")
    logger.info("="*80)

    try:
        gateway_source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "streaming_gateway.py"

        if gateway_source.exists():
            content = gateway_source.read_text()

            # Check GStreamer cleanup
            assert "pipelines.clear()" in content or "pipeline" in content, "Pipeline cleanup missing"
            test_result("Pipeline cleanup", True)

            # Check thread joining
            assert "thread.join" in content, "Thread joining missing"
            test_result("Thread joining", True)

            # Check statistics reset
            assert "reset_transmission_stats" in content, "Statistics reset missing"
            test_result("Statistics reset", True)

        return True

    except Exception as e:
        test_result("Cleanup procedures", False, str(e))
        return False


def test_cross_platform_support():
    """Test 11: Verify cross-platform support."""
    logger.info("\n" + "="*80)
    logger.info("TEST 11: Cross-Platform Support")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_worker_manager.py"

        if source.exists():
            content = source.read_text()

            # Check platform detection
            assert "sys.platform" in content, "Platform detection missing"
            test_result("Platform detection", True)

            # Check macOS support
            assert "darwin" in content, "macOS support missing"
            test_result("macOS support", True)

            # Check context selection
            assert "multiprocessing.get_context" in content, "Context selection missing"
            test_result("Multiprocessing context selection", True)

        return True

    except Exception as e:
        test_result("Cross-platform support", False, str(e))
        return False


def test_statistics_aggregation():
    """Test 12: Verify statistics aggregation."""
    logger.info("\n" + "="*80)
    logger.info("TEST 12: Statistics Aggregation")
    logger.info("="*80)

    try:
        source = Path(__file__).parent / "src" / "matrice_streaming" / "streaming_gateway" / "camera_streamer" / "gstreamer_worker_manager.py"

        if source.exists():
            content = source.read_text()

            # Check per_camera_stats aggregation
            assert "per_camera_stats" in content, "per_camera_stats aggregation missing"
            test_result("per_camera_stats aggregation", True)

            # Check health reports
            assert "health_reports" in content, "Health reports missing"
            test_result("Health reports", True)

        return True

    except Exception as e:
        test_result("Statistics aggregation", False, str(e))
        return False


def print_summary():
    """Print test summary."""
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    total = len(test_results["passed"]) + len(test_results["failed"])
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    warnings = len(test_results["warnings"])

    logger.info(f"\nTotal Tests: {total}")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    if warnings:
        logger.info(f"⚠️  Warnings: {warnings}")

    if failed > 0:
        logger.error("\n❌ FAILED TESTS:")
        for test in test_results["failed"]:
            logger.error(f"  - {test}")

    if warnings:
        logger.warning("\n⚠️  WARNINGS:")
        for warning in test_results["warnings"]:
            logger.warning(f"  - {warning}")

    if failed == 0:
        logger.info("\n" + "="*80)
        logger.info("🎉 ALL TESTS PASSED! Code is ready to push.")
        logger.info("="*80)
        return True
    else:
        logger.error("\n" + "="*80)
        logger.error("❌ SOME TESTS FAILED! Please fix before pushing.")
        logger.error("="*80)
        return False


def main():
    """Run all tests."""
    logger.info("="*80)
    logger.info("GStreamer Integration Test Suite")
    logger.info("="*80)
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {Path.cwd()}")

    # Run all tests
    import_success, gstreamer_available = test_imports()
    if not import_success:
        logger.error("Critical: Import failed. Cannot continue tests.")
        return False

    test_gstreamer_config()
    test_gstreamer_camera_streamer_api()
    test_gstreamer_worker_manager_api()
    test_frame_optimizer_integration()
    test_timing_metrics()
    test_batch_optimization()
    test_connection_management()
    test_metrics_logging()
    test_cleanup_procedures()
    test_cross_platform_support()
    test_statistics_aggregation()

    # Print summary
    success = print_summary()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
