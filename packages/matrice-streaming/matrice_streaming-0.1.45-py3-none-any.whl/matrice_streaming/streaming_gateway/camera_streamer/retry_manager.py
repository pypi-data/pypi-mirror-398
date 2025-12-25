"""Retry management for robust connection handling."""
import logging
import time
from typing import Optional


class RetryConfig:
    """Configuration for retry logic."""
    MAX_CONSECUTIVE_FAILURES = 10
    MIN_RETRY_COOLDOWN = 5
    MAX_RETRY_COOLDOWN = 30
    RECONNECT_PAUSE = 1.0
    READ_FAILURE_PAUSE = 0.1


class RetryManager:
    """Manages retry logic and connection state with infinite retries."""
    
    def __init__(self, stream_key: str):
        """Initialize retry manager.
        
        Args:
            stream_key: Stream identifier for logging
        """
        self.stream_key = stream_key
        self.retry_cycle = 0
        self.consecutive_failures = 0
        self.logger = logging.getLogger(__name__)
    
    def should_reconnect(self) -> bool:
        """Check if should reconnect due to consecutive failures.
        
        Returns:
            True if should reconnect
        """
        if self.consecutive_failures >= RetryConfig.MAX_CONSECUTIVE_FAILURES:
            self.logger.error(
                f"Too many consecutive failures for {self.stream_key} "
                f"({self.consecutive_failures}), will reconnect"
            )
            return True
        return False
    
    def record_read_failure(self):
        """Record a frame read failure."""
        self.consecutive_failures += 1
        self.logger.warning(
            f"Frame read failed for {self.stream_key} "
            f"(consecutive: {self.consecutive_failures})"
        )
    
    def record_success(self):
        """Record a successful operation (resets failure counter)."""
        self.consecutive_failures = 0
    
    def handle_connection_failure(self, error: Exception):
        """Handle connection failure and calculate backoff.
        
        Args:
            error: The exception that occurred
        """
        self.retry_cycle += 1
        self.logger.error(
            f"Streaming error for {self.stream_key} "
            f"(retry cycle {self.retry_cycle}): {error}"
        )
    
    def handle_successful_reconnect(self):
        """Handle successful reconnection."""
        if self.retry_cycle > 0:
            self.logger.info(
                f"Successfully reconnected {self.stream_key} "
                f"after {self.retry_cycle} retry cycles"
            )
        self.retry_cycle = 0
        self.consecutive_failures = 0
    
    def wait_before_retry(self):
        """Wait with exponential backoff before retry.
        
        This implements exponential backoff with a maximum cooldown.
        The system will NEVER give up - it retries forever.
        """
        cooldown = min(
            RetryConfig.MAX_RETRY_COOLDOWN,
            RetryConfig.MIN_RETRY_COOLDOWN + self.retry_cycle
        )
        self.logger.info(
            f"Waiting {cooldown}s before retry cycle {self.retry_cycle + 1} "
            f"for {self.stream_key} (will retry forever)"
        )
        time.sleep(cooldown)
    
    def wait_after_read_failure(self):
        """Brief pause after read failure before retrying."""
        time.sleep(RetryConfig.READ_FAILURE_PAUSE)
    
    def wait_before_restart(self):
        """Brief pause before restarting video file."""
        time.sleep(RetryConfig.RECONNECT_PAUSE)
    
    def get_stats(self) -> dict:
        """Get retry statistics.
        
        Returns:
            Dictionary with retry statistics
        """
        return {
            "retry_cycle": self.retry_cycle,
            "consecutive_failures": self.consecutive_failures,
            "stream_key": self.stream_key,
        }

