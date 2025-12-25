"""Test script for Phase 1: Async infrastructure.

Tests the async camera worker and encoding pool manager with a small
number of cameras to validate the architecture works correctly.
"""
import sys
import logging
import multiprocessing
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_streaming.streaming_gateway.camera_streamer.encoding_pool_manager import EncodingPoolManager
from matrice_streaming.streaming_gateway.camera_streamer.async_camera_worker import run_async_worker


def test_phase1_infrastructure():
    """Test Phase 1: Infrastructure with 2 workers, 4 cameras."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("="*60)
    logger.info("PHASE 1 INFRASTRUCTURE TEST")
    logger.info("="*60)

    # Test configuration
    NUM_WORKERS = 2
    CAMERAS_PER_WORKER = 2
    TEST_DURATION = 10  # seconds

    # Use a test video file if available, otherwise use camera 0
    test_source = 0  # Webcam

    # Create camera configurations
    all_cameras = []
    for worker_id in range(NUM_WORKERS):
        worker_cameras = []
        for cam_id in range(CAMERAS_PER_WORKER):
            camera_idx = worker_id * CAMERAS_PER_WORKER + cam_id
            camera_config = {
                'stream_key': f'test_camera_{camera_idx}',
                'stream_group_key': 'test_group',
                'source': test_source,
                'topic': f'test_topic_{camera_idx}',
                'fps': 10,
                'quality': 80,
                'width': 640,
                'height': 480,
                'camera_location': f'Test Location {camera_idx}'
            }
            worker_cameras.append(camera_config)
        all_cameras.append(worker_cameras)

    # Stream configuration (Redis)
    stream_config = {
        'service_id': 'test_streaming_gateway',
        'host': 'localhost',
        'port': 6379,
        'enable_batching': True,
        'batch_size': 10,
        'batch_timeout': 0.5,
        'pool_max_connections': 20
    }

    # Create multiprocessing primitives
    stop_event = multiprocessing.Event()
    health_queue = multiprocessing.Queue()
    manager = multiprocessing.Manager()

    # Start encoding pool
    logger.info(f"Starting encoding pool...")
    encoding_pool_mgr = EncodingPoolManager(num_workers=4)
    encoding_pool_mgr.start()
    encoding_pool = encoding_pool_mgr.get_pool()

    # Start worker processes
    workers = []
    logger.info(f"Starting {NUM_WORKERS} worker processes...")
    for worker_id in range(NUM_WORKERS):
        worker = multiprocessing.Process(
            target=run_async_worker,
            args=(
                worker_id,
                all_cameras[worker_id],
                stream_config,
                encoding_pool,
                stop_event,
                health_queue
            ),
            name=f"Worker-{worker_id}"
        )
        worker.start()
        workers.append(worker)
        logger.info(f"Started worker {worker_id} with {len(all_cameras[worker_id])} cameras")

    # Monitor for test duration
    logger.info(f"Running test for {TEST_DURATION} seconds...")
    logger.info("Monitoring health reports...")

    start_time = time.time()
    health_reports = {}

    try:
        while time.time() - start_time < TEST_DURATION:
            # Check health reports
            while not health_queue.empty():
                report = health_queue.get()
                worker_id = report['worker_id']
                health_reports[worker_id] = report

                logger.info(
                    f"Health: Worker {report['worker_id']} - "
                    f"Status: {report['status']}, "
                    f"Active cameras: {report['active_cameras']}"
                )

            # Check worker processes
            for i, worker in enumerate(workers):
                if not worker.is_alive():
                    logger.error(f"Worker {i} died unexpectedly!")

            time.sleep(1.0)

        logger.info(f"Test duration complete!")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")

    finally:
        # Shutdown
        logger.info("Shutting down workers...")
        stop_event.set()

        # Wait for workers to finish
        for i, worker in enumerate(workers):
            worker.join(timeout=10.0)
            if worker.is_alive():
                logger.warning(f"Worker {i} did not stop gracefully, terminating...")
                worker.terminate()
                worker.join(timeout=5.0)
            logger.info(f"Worker {i} stopped")

        # Stop encoding pool
        logger.info("Stopping encoding pool...")
        encoding_pool_mgr.stop()

        # Final health check
        logger.info("\n" + "="*60)
        logger.info("FINAL HEALTH REPORT")
        logger.info("="*60)
        for worker_id, report in health_reports.items():
            logger.info(
                f"Worker {worker_id}: "
                f"Status={report['status']}, "
                f"Cameras={report['active_cameras']}, "
                f"Error={report.get('error', 'None')}"
            )

        logger.info("="*60)
        logger.info("TEST COMPLETE")
        logger.info("="*60)


if __name__ == '__main__':
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()

    test_phase1_infrastructure()
