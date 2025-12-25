"""Comprehensive E2E tests for production deployment.

This test suite validates the complete streaming pipeline from camera capture
through encoding, batching, and Redis storage.
"""
import sys
import time
import logging
import asyncio
import multiprocessing
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_streaming.streaming_gateway.camera_streamer.worker_manager import WorkerManager


def create_test_cameras(num_cameras: int) -> list:
    """Create camera configurations for testing.

    Args:
        num_cameras: Number of cameras to create

    Returns:
        List of camera configurations
    """
    cameras = []
    test_video = str(Path(__file__).parent / "test_video.mp4")

    for i in range(num_cameras):
        camera_config = {
            'stream_key': f'e2e_camera_{i:04d}',
            'stream_group_key': f'e2e_group_{i // 10}',
            'source': test_video,
            'topic': f'e2e_test_stream_{i // 25}',  # 25 cameras per topic
            'fps': 10,
            'quality': 70,
            'width': 640,
            'height': 480,
            'camera_location': f'E2E_Location_{i}'
        }
        cameras.append(camera_config)

    return cameras


def test_e2e_basic_flow():
    """Test E2E flow with 20 cameras for 15 seconds.

    This validates:
    - Worker startup and initialization
    - Camera capture and encoding
    - Redis message batching and sending
    - Health monitoring
    - Graceful shutdown
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("E2E TEST: Basic Flow (20 cameras, 15 seconds)")
    logger.info("="*70)

    # Configuration
    NUM_CAMERAS = 20
    NUM_WORKERS = 4
    DURATION = 15

    cameras = create_test_cameras(NUM_CAMERAS)

    stream_config = {
        'service_id': 'e2e_test_gateway',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 50,
        'batch_timeout': 0.1,
        'pool_max_connections': 50
    }

    logger.info(f"Configuration:")
    logger.info(f"  Cameras: {NUM_CAMERAS}")
    logger.info(f"  Workers: {NUM_WORKERS}")
    logger.info(f"  Duration: {DURATION}s")
    logger.info(f"  Expected frames: ~{NUM_CAMERAS * 10 * DURATION}")
    logger.info(f"  Batching: enabled (size={stream_config['batch_size']}, timeout={stream_config['batch_timeout']})")

    # Create manager
    manager = WorkerManager(
        camera_configs=cameras,
        stream_config=stream_config,
        num_workers=NUM_WORKERS
    )

    try:
        # Run test
        start_time = time.time()
        manager.run(duration=DURATION)
        elapsed = time.time() - start_time

        # Verify results
        logger.info("\n" + "="*70)
        logger.info("E2E TEST RESULTS:")
        logger.info("="*70)

        success = True

        # Check 1: Duration
        if abs(elapsed - DURATION) > 2.0:
            logger.error(f"[FAIL] Duration check failed: {elapsed:.1f}s (expected ~{DURATION}s)")
            success = False
        else:
            logger.info(f"[PASS] Duration: {elapsed:.1f}s")

        # Check 2: All workers started
        if len(manager.workers) != NUM_WORKERS:
            logger.error(f"[FAIL] Worker count: {len(manager.workers)} (expected {NUM_WORKERS})")
            success = False
        else:
            logger.info(f"[PASS] Workers started: {NUM_WORKERS}")

        # Check 3: Workers exited cleanly
        normal_exits = sum(1 for w in manager.workers if w.exitcode == 0)
        if normal_exits != NUM_WORKERS:
            logger.error(f"[FAIL] Clean exits: {normal_exits}/{NUM_WORKERS}")
            success = False
        else:
            logger.info(f"[PASS] All workers exited cleanly: {normal_exits}/{NUM_WORKERS}")

        # Check 4: Health reports received
        if not manager.last_health_reports:
            logger.error(f"[FAIL] No health reports received")
            success = False
        else:
            logger.info(f"[PASS] Health reports received: {len(manager.last_health_reports)} workers")

            # Check all workers reported running status
            running_count = sum(
                1 for report in manager.last_health_reports.values()
                if report.get('status') == 'running'
            )
            if running_count < NUM_WORKERS:
                logger.warning(f"  Note: Only {running_count}/{NUM_WORKERS} reported running")

        logger.info("\n" + "="*70)
        if success:
            logger.info("[PASS] E2E BASIC FLOW TEST PASSED")
        else:
            logger.error("[FAIL] E2E BASIC FLOW TEST FAILED")
        logger.info("="*70)

        return success

    except Exception as exc:
        logger.error(f"Test failed with exception: {exc}", exc_info=True)
        return False


def test_e2e_scaling_100_cameras():
    """Test E2E flow with 100 cameras for 20 seconds.

    This validates scaling performance and resource usage.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("E2E TEST: Scaling (100 cameras, 20 workers, 20 seconds)")
    logger.info("="*70)

    # Configuration
    NUM_CAMERAS = 100
    NUM_WORKERS = 20
    DURATION = 20

    cameras = create_test_cameras(NUM_CAMERAS)

    stream_config = {
        'service_id': 'e2e_scaling_gateway',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 50,
        'batch_timeout': 0.1,
        'pool_max_connections': 50
    }

    logger.info(f"Configuration:")
    logger.info(f"  Cameras: {NUM_CAMERAS}")
    logger.info(f"  Workers: {NUM_WORKERS}")
    logger.info(f"  Duration: {DURATION}s")
    logger.info(f"  Expected frames: ~{NUM_CAMERAS * 10 * DURATION} ({NUM_CAMERAS * 10} FPS)")
    logger.info(f"  Batching: enabled")

    # Track memory usage
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / (1024**3)
        logger.info(f"  Starting memory: {start_memory:.2f} GB")
    except ImportError:
        logger.warning("  psutil not available - skipping memory tracking")
        start_memory = None

    # Create manager
    manager = WorkerManager(
        camera_configs=cameras,
        stream_config=stream_config,
        num_workers=NUM_WORKERS
    )

    try:
        # Run test
        start_time = time.time()
        manager.run(duration=DURATION)
        elapsed = time.time() - start_time

        # Check memory
        if start_memory is not None:
            end_memory = process.memory_info().rss / (1024**3)
            memory_increase = end_memory - start_memory
            logger.info(f"  Ending memory: {end_memory:.2f} GB (increase: {memory_increase:.2f} GB)")

        # Verify results
        logger.info("\n" + "="*70)
        logger.info("E2E SCALING TEST RESULTS:")
        logger.info("="*70)

        success = True

        # Check 1: All workers started
        if len(manager.workers) != NUM_WORKERS:
            logger.error(f"[FAIL] Worker count: {len(manager.workers)} (expected {NUM_WORKERS})")
            success = False
        else:
            logger.info(f"[PASS] Workers started: {NUM_WORKERS}")

        # Check 2: Workers exited cleanly
        normal_exits = sum(1 for w in manager.workers if w.exitcode == 0)
        if normal_exits != NUM_WORKERS:
            logger.error(f"[FAIL] Clean exits: {normal_exits}/{NUM_WORKERS}")
            success = False
        else:
            logger.info(f"[PASS] All workers exited cleanly: {normal_exits}/{NUM_WORKERS}")

        # Check 3: Performance
        if elapsed > DURATION + 5:
            logger.warning(f"[WARN] Test took longer than expected: {elapsed:.1f}s vs {DURATION}s")
        else:
            logger.info(f"[PASS] Performance: {elapsed:.1f}s")

        # Check 4: Memory usage (if available)
        if start_memory is not None and end_memory > 15.0:
            logger.warning(f"[WARN] Memory usage high: {end_memory:.2f} GB (target < 15 GB)")
        elif start_memory is not None:
            logger.info(f"[PASS] Memory usage: {end_memory:.2f} GB")

        logger.info("\n" + "="*70)
        if success:
            logger.info("[PASS] E2E SCALING TEST PASSED")
        else:
            logger.error("[FAIL] E2E SCALING TEST FAILED")
        logger.info("="*70)

        return success

    except Exception as exc:
        logger.error(f"Test failed with exception: {exc}", exc_info=True)
        return False


def test_e2e_redis_verification():
    """Test E2E flow and verify frames in Redis.

    This validates that messages actually reach Redis with correct batching.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("E2E TEST: Redis Verification (10 cameras, 10 seconds)")
    logger.info("="*70)

    # Configuration
    NUM_CAMERAS = 10
    NUM_WORKERS = 2
    DURATION = 10

    cameras = create_test_cameras(NUM_CAMERAS)

    stream_config = {
        'service_id': 'e2e_redis_test',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 50,
        'batch_timeout': 0.1,
        'pool_max_connections': 50
    }

    logger.info(f"Configuration:")
    logger.info(f"  Cameras: {NUM_CAMERAS}")
    logger.info(f"  Duration: {DURATION}s")
    logger.info(f"  Expected frames: ~{NUM_CAMERAS * 10 * DURATION}")

    # Create manager
    manager = WorkerManager(
        camera_configs=cameras,
        stream_config=stream_config,
        num_workers=NUM_WORKERS
    )

    try:
        # Clear Redis streams before test
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=False)

            # Delete test streams
            unique_topics = set(cam['topic'] for cam in cameras)
            for topic in unique_topics:
                try:
                    r.delete(topic)
                    logger.info(f"  Cleared stream: {topic}")
                except Exception as e:
                    logger.warning(f"  Could not clear {topic}: {e}")

            r.close()
        except ImportError:
            logger.warning("  redis-py not available - skipping stream cleanup")
        except Exception as e:
            logger.warning(f"  Could not connect to Redis: {e}")

        # Run test
        logger.info("\nStarting streaming...")
        manager.run(duration=DURATION)

        # Verify frames in Redis
        logger.info("\n" + "="*70)
        logger.info("VERIFYING FRAMES IN REDIS:")
        logger.info("="*70)

        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=False)

            total_frames = 0
            unique_topics = set(cam['topic'] for cam in cameras)

            for topic in sorted(unique_topics):
                try:
                    frame_count = r.xlen(topic)
                    total_frames += frame_count
                    cameras_in_topic = sum(1 for cam in cameras if cam['topic'] == topic)
                    expected = cameras_in_topic * 10 * DURATION

                    logger.info(f"  {topic}: {frame_count} frames (expected ~{expected})")

                    # Check we got at least 50% of expected frames (accounting for startup/shutdown)
                    if frame_count < expected * 0.5:
                        logger.warning(f"    [WARN] Low frame count: {frame_count} < {expected * 0.5:.0f}")

                except Exception as e:
                    logger.error(f"  Error checking {topic}: {e}")

            expected_total = NUM_CAMERAS * 10 * DURATION
            logger.info(f"\nTotal frames in Redis: {total_frames}")
            logger.info(f"Expected frames: ~{expected_total}")
            logger.info(f"Capture rate: {100 * total_frames / expected_total:.1f}%")

            r.close()

            # Consider test successful if we got at least 70% of frames
            success = total_frames >= expected_total * 0.7

            if success:
                logger.info("\n[PASS] Redis verification PASSED")
            else:
                logger.error("\n[FAIL] Redis verification FAILED - too few frames")

            return success

        except ImportError:
            logger.error("[FAIL] redis-py not installed - cannot verify frames")
            return False
        except Exception as e:
            logger.error(f"[FAIL] Redis verification failed: {e}")
            return False

    except Exception as exc:
        logger.error(f"Test failed with exception: {exc}", exc_info=True)
        return False


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()

    import argparse

    parser = argparse.ArgumentParser(description='E2E production tests')
    parser.add_argument(
        '--test',
        choices=['basic', 'scaling', 'redis', 'all'],
        default='all',
        help='Which test to run'
    )

    args = parser.parse_args()

    results = {}

    if args.test in ['basic', 'all']:
        print("\n" + "="*70)
        print("RUNNING: E2E Basic Flow Test")
        print("="*70)
        results['basic'] = test_e2e_basic_flow()
        time.sleep(2)

    if args.test in ['scaling', 'all']:
        print("\n" + "="*70)
        print("RUNNING: E2E Scaling Test")
        print("="*70)
        results['scaling'] = test_e2e_scaling_100_cameras()
        time.sleep(2)

    if args.test in ['redis', 'all']:
        print("\n" + "="*70)
        print("RUNNING: E2E Redis Verification Test")
        print("="*70)
        results['redis'] = test_e2e_redis_verification()

    # Print summary
    print("\n" + "="*70)
    print("E2E TEST SUITE SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "[PASS] PASSED" if passed else "[FAIL] FAILED"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())

    print("="*70)
    if all_passed:
        print("[PASS] ALL E2E TESTS PASSED - READY FOR PRODUCTION")
    else:
        print("[FAIL] SOME E2E TESTS FAILED - NOT READY FOR PRODUCTION")
    print("="*70)

    sys.exit(0 if all_passed else 1)
