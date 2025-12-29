"""Test script for Phase 2: Scaling to 20 workers with 1000 cameras.

This tests the full production architecture with realistic load.
"""
import sys
import logging
import multiprocessing
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_streaming.streaming_gateway.camera_streamer.worker_manager import WorkerManager


def create_test_cameras(num_cameras: int, use_webcam: bool = False) -> list:
    """Create camera configurations for testing.

    Args:
        num_cameras: Number of cameras to create
        use_webcam: If True, use webcam (0), otherwise use test pattern

    Returns:
        List of camera configurations
    """
    cameras = []

    # Use webcam or create mock sources
    if use_webcam:
        # Single webcam shared across all "cameras"
        source = 0
    else:
        # Create a simple test video file path (will be created if doesn't exist)
        source = str(Path(__file__).parent / "test_video.mp4")

    for i in range(num_cameras):
        camera_config = {
            'stream_key': f'camera_{i:04d}',
            'stream_group_key': f'group_{i // 10}',  # 10 cameras per group
            'source': source,
            'topic': f'test_stream_{i // 50}',  # 50 cameras per topic
            'fps': 10,  # Lower FPS for testing
            'quality': 70,  # Lower quality for faster encoding
            'width': 640,
            'height': 480,
            'camera_location': f'Test_Location_{i}'
        }
        cameras.append(camera_config)

    return cameras


def test_phase2_small(duration: int = 20):
    """Test Phase 2 with 100 cameras (small scale test).

    Args:
        duration: Test duration in seconds
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("PHASE 2 TEST: 20 Workers + 100 Cameras (Small Scale)")
    logger.info("="*70)

    # Create camera configurations
    NUM_CAMERAS = 100
    NUM_WORKERS = 20
    cameras = create_test_cameras(NUM_CAMERAS, use_webcam=False)

    # Stream configuration
    stream_config = {
        'service_id': 'test_streaming_gateway',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 50,
        'batch_timeout': 0.1,
        'pool_max_connections': 50
    }

    logger.info(f"Configuration:")
    logger.info(f"  - Cameras: {NUM_CAMERAS}")
    logger.info(f"  - Workers: {NUM_WORKERS}")
    logger.info(f"  - Expected: {NUM_CAMERAS // NUM_WORKERS} cameras per worker")
    logger.info(f"  - Duration: {duration} seconds")
    logger.info(f"  - Target throughput: {NUM_CAMERAS * 10} FPS")

    # Create and run worker manager
    manager = WorkerManager(
        camera_configs=cameras,
        stream_config=stream_config,
        num_workers=NUM_WORKERS
    )

    try:
        manager.run(duration=duration)

        logger.info("\n" + "="*70)
        logger.info("TEST COMPLETE - Check results:")
        logger.info("="*70)
        logger.info("1. All workers should have started and stopped cleanly")
        logger.info("2. Health reports should show 'running' status")
        logger.info("3. Each worker should handle 5 cameras")
        logger.info("4. Redis should contain frames from all cameras")
        logger.info("\nTo verify frames in Redis:")
        logger.info("  redis-cli")
        logger.info("  > KEYS test_stream_*")
        logger.info("  > XLEN test_stream_0")

    except Exception as exc:
        logger.error(f"Test failed: {exc}", exc_info=True)
        return False

    return True


def test_phase2_full(duration: int = 30):
    """Test Phase 2 with 1000 cameras (full scale test).

    Args:
        duration: Test duration in seconds
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("PHASE 2 TEST: 20 Workers + 1000 Cameras (FULL SCALE)")
    logger.info("="*70)

    # Create camera configurations
    NUM_CAMERAS = 1000
    NUM_WORKERS = 20
    cameras = create_test_cameras(NUM_CAMERAS, use_webcam=False)

    # Stream configuration
    stream_config = {
        'service_id': 'production_streaming_gateway',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 50,
        'batch_timeout': 0.1,
        'pool_max_connections': 50
    }

    logger.info(f"Configuration:")
    logger.info(f"  - Cameras: {NUM_CAMERAS}")
    logger.info(f"  - Workers: {NUM_WORKERS}")
    logger.info(f"  - Expected: {NUM_CAMERAS // NUM_WORKERS} cameras per worker")
    logger.info(f"  - Duration: {duration} seconds")
    logger.info(f"  - Target throughput: {NUM_CAMERAS * 10} = 10,000 FPS")
    logger.info("")
    logger.info("PERFORMANCE TARGETS:")
    logger.info("  - Memory usage: < 15 GB (vs 100 GB with threading)")
    logger.info("  - Throughput: ~10,000 FPS")
    logger.info("  - Latency: < 100ms per frame")

    # Create and run worker manager
    manager = WorkerManager(
        camera_configs=cameras,
        stream_config=stream_config,
        num_workers=NUM_WORKERS
    )

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / (1024**3)  # GB

        logger.info(f"\nStarting memory usage: {start_memory:.2f} GB")

        manager.run(duration=duration)

        end_memory = process.memory_info().rss / (1024**3)  # GB
        memory_increase = end_memory - start_memory

        logger.info("\n" + "="*70)
        logger.info("PERFORMANCE RESULTS:")
        logger.info("="*70)
        logger.info(f"Memory usage: {end_memory:.2f} GB (increase: {memory_increase:.2f} GB)")
        logger.info(f"Target: < 15 GB")
        logger.info(f"Result: {'PASS' if end_memory < 15 else 'FAIL'}")

        # Calculate expected frames
        expected_frames = NUM_CAMERAS * 10 * duration  # cameras * fps * duration
        logger.info(f"\nExpected frames sent: ~{expected_frames:,}")
        logger.info("Verify in Redis with: redis-cli KEYS test_stream_* | xargs -I {} redis-cli XLEN {}")

    except Exception as exc:
        logger.error(f"Test failed: {exc}", exc_info=True)
        return False

    return True


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()

    import argparse

    parser = argparse.ArgumentParser(description='Phase 2 scaling tests')
    parser.add_argument(
        '--scale',
        choices=['small', 'full'],
        default='small',
        help='Test scale: small (100 cameras) or full (1000 cameras)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=20,
        help='Test duration in seconds (default: 20)'
    )

    args = parser.parse_args()

    if args.scale == 'small':
        success = test_phase2_small(duration=args.duration)
    else:
        success = test_phase2_full(duration=args.duration)

    sys.exit(0 if success else 1)
