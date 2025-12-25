"""Encoding process pool manager for CPU-bound frame encoding operations.

This module manages a pool of worker processes dedicated to CPU-intensive
frame encoding tasks (JPEG compression, H265 encoding, etc.).
"""
import logging
import multiprocessing
import os
from typing import Optional


class EncodingPoolManager:
    """Manages a process pool for parallel frame encoding.

    The encoding pool handles CPU-bound operations in separate processes
    to bypass the GIL and achieve true parallel execution on multi-core systems.
    """

    def __init__(self, num_workers: Optional[int] = None):
        """Initialize encoding pool manager.

        Args:
            num_workers: Number of encoding workers (default: CPU_count - 2)
        """
        if num_workers is None:
            # Reserve 2 cores for main process and I/O workers
            cpu_count = multiprocessing.cpu_count()
            num_workers = max(2, cpu_count - 2)

        self.num_workers = num_workers
        self.pool: Optional[multiprocessing.Pool] = None
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            f"Encoding pool manager initialized with {num_workers} workers "
            f"(CPU count: {multiprocessing.cpu_count()})"
        )

    def start(self):
        """Start the encoding process pool."""
        if self.pool is not None:
            self.logger.warning("Encoding pool already started")
            return

        try:
            # Create process pool with maxtasksperchild to prevent memory leaks
            self.pool = multiprocessing.Pool(
                processes=self.num_workers,
                maxtasksperchild=1000  # Recycle workers after 1000 tasks
            )
            self.logger.info(f"Started encoding pool with {self.num_workers} workers")

        except Exception as exc:
            self.logger.error(f"Failed to start encoding pool: {exc}")
            raise

    def stop(self, timeout: float = 10.0):
        """Stop the encoding process pool gracefully.

        Args:
            timeout: Maximum time to wait for workers to finish (seconds)
        """
        if self.pool is None:
            self.logger.warning("Encoding pool not running")
            return

        try:
            self.logger.info("Stopping encoding pool...")

            # Close pool (no more tasks accepted)
            self.pool.close()

            # Wait for workers to finish with timeout
            self.pool.join(timeout)

            self.logger.info("Encoding pool stopped")

        except Exception as exc:
            self.logger.error(f"Error stopping encoding pool: {exc}")

            # Force terminate if graceful shutdown fails
            try:
                self.pool.terminate()
                self.pool.join(timeout=5.0)
                self.logger.warning("Encoding pool forcefully terminated")
            except Exception as term_exc:
                self.logger.error(f"Failed to terminate encoding pool: {term_exc}")

        finally:
            self.pool = None

    def get_pool(self) -> multiprocessing.Pool:
        """Get the encoding process pool.

        Returns:
            Process pool instance

        Raises:
            RuntimeError: If pool is not started
        """
        if self.pool is None:
            raise RuntimeError("Encoding pool not started. Call start() first.")
        return self.pool

    def is_running(self) -> bool:
        """Check if encoding pool is running.

        Returns:
            True if pool is active
        """
        return self.pool is not None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def _init_worker():
    """Initialize worker process.

    This runs once per worker process on startup.
    Can be used to set up per-worker resources.
    """
    # Set process affinity if needed
    # os.sched_setaffinity(0, {cpu_id})

    # Setup minimal logging for workers
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - EncodingWorker - %(levelname)s - %(message)s'
    )
