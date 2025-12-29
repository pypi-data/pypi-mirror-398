"""
Streaming Orchestrator - Auto-manages streaming gateway lifecycle.

This module provides a high-level orchestrator that takes a streaming_gateway_id and session
and automatically manages the entire streaming lifecycle including setup, start, monitoring,
and cleanup.
"""

import logging
import time
import threading
from typing import Dict, Optional
from matrice_common.session import Session
from matrice_common.rpc import RPC
from .streaming_gateway import StreamingGateway
from .streaming_gateway_utils import StreamingGatewayUtil
from .metrics_reporter import MetricsManager, MetricsConfig
from .streaming_status_listener import StreamingStatusListener


class StreamingAction:
    """
    High-level orchestrator for streaming gateway lifecycle management.

    This class automates the entire streaming process:
    1. Fetches configuration from API using streaming_gateway_id
    2. Sets up StreamingGateway with proper configuration
    3. Starts streaming with status updates to API
    4. Monitors streaming health
    5. Periodically checks if action ID matches streaming gateway's actionRecordID
    6. Automatically stops if action ID mismatch is detected
    7. Handles errors and recovery
    8. Provides clean shutdown

    Example usage:
        orchestrator = StreamingAction(
            session=session,
            action_id="your_action_id",
            action_id_check_interval=30.0,  # Check every 30 seconds
        )

        # Start streaming (auto-fetches config, sets up, and starts)
        if orchestrator.start():
            logging.info("Streaming started successfully!")

            # Monitor for a while
            time.sleep(60)

            # Stop when done
            orchestrator.stop()
        else:
            logging.error("Failed to start streaming")
    """

    def __init__(
        self,
        session: Session,
        action_id: str,
        enable_intelligent_transmission: bool = True,
        monitoring_interval: float = 30.0,  # Heartbeat sent every monitoring_interval seconds
        auto_restart: bool = True,
        max_restart_attempts: int = 3,
        action_id_check_interval: float = 600.0,  # 10 minutes (was 60 seconds)
        enable_event_listening: bool = True,
        allow_empty_start: bool = True,  # Allow starting with zero cameras
    ):
        """Initialize StreamingAction.

        Args:
            session: Session object for authentication
            action_id: ID of the action to manage
            enable_intelligent_transmission: Whether to enable intelligent frame transmission
            monitoring_interval: Interval in seconds between health checks and heartbeats (default: 30 seconds)
            auto_restart: Whether to automatically restart on failures
            max_restart_attempts: Maximum number of restart attempts before giving up
            action_id_check_interval: Interval in seconds between checks to verify action ID matches streaming gateway
            enable_event_listening: Enable dynamic event listening for configuration updates
            allow_empty_start: Allow starting with zero cameras (default True). Cameras can be added dynamically.
        """
        if not session:
            raise ValueError("Session is required")

        if not action_id:
            raise ValueError("action_id is required")

        self.session = session
        self.rpc: RPC = session.rpc
        self.action_id = action_id

        # Fetch action details from API
        try:
            url = f"/v1/actions/action/{self.action_id}/details"
            response = self.rpc.get(url)
            if not response.get("success", False):
                raise RuntimeError(
                    f"Failed to fetch action details: {response.get('message', 'Unknown error')}"
                )

            self.action_doc = response["data"]
            self.action_type = self.action_doc["action"]
            self.project_id = self.action_doc["_idProject"]
            self.streaming_gateway_id = self.action_doc["_idService"]

            logging.info(
                "Action doc retrieved successfully for action_id: %s", self.action_id
            )
            logging.debug("Action doc: %s", self.action_doc)

            self.action_details = self.action_doc.get("actionDetails", {})
            logging.debug("Action details: %s", self.action_details)

            self.job_params = self.action_doc.get("jobParams", {})
            logging.debug("Job params: %s", self.job_params)

            self.account_number = self.action_doc.get("account_number", "")
            logging.info("Account number: %s", self.account_number)

            self.server_id = self.action_details["serverId"]
            self.server_type = self.action_details["serverType"]
            self.video_codec = self.action_details["video_codec"]

            self.video_codec = self.action_details.get(
                "video_codec", self.job_params.get("video_codec", "h264")
            )

        except Exception as exc:
            logging.error(
                "Failed to initialize StreamingAction: %s", str(exc), exc_info=True
            )
            raise RuntimeError(
                f"Failed to initialize StreamingAction: {str(exc)}"
            ) from exc

        # Acknowledge action initialization
        # self.update_status(
        #     "STG_ACK",
        #     "ACK",
        #     "Action is acknowledged by streaming gateway",
        # )

        self.enable_intelligent_transmission = enable_intelligent_transmission
        self.monitoring_interval = monitoring_interval
        self.auto_restart = auto_restart
        self.max_restart_attempts = max_restart_attempts
        self.action_id_check_interval = action_id_check_interval
        self.enable_event_listening = enable_event_listening
        self.allow_empty_start = allow_empty_start

        # Initialize utility and gateway objects
        self.gateway_util = StreamingGatewayUtil(
            session, self.streaming_gateway_id, self.server_id, action_id=self.action_id
        )
        self.streaming_gateway: Optional[StreamingGateway] = None

        # State management
        self._is_running = False
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._restart_attempts = 0
        self._state_lock = threading.RLock()
        self._last_action_id_check_time = 0.0

        # Statistics
        self.stats = {
            "start_time": None,
            "total_uptime": 0.0,
            "restart_count": 0,
            "last_restart_time": None,
            "health_checks": 0,
            "health_check_failures": 0,
            "action_id_checks": 0,
            "action_id_check_failures": 0,
            "current_status": "initialized",
            "last_error": None,
            "last_error_time": None,
        }

        # Initialize metrics manager
        self.metrics_manager: Optional[MetricsManager] = None

        # Initialize status listener for stop commands
        self.status_listener: Optional[StreamingStatusListener] = None

        logging.info(
            "StreamingAction initialized successfully for gateway: %s",
            self.streaming_gateway_id,
        )

    def update_status(self, step_code: str, status: str, status_description: str):
        """Update the status of the data processing job."""
        try:
            logging.info(
                "Updating action status - Step: %s, Status: %s, Description: %s",
                step_code,
                status,
                status_description,
            )

            url = "/v1/actions"
            payload = {
                "_id": self.action_id,
                "action": self.action_type,
                "serviceName": self.action_doc["serviceName"],
                "stepCode": step_code,
                "status": status,
                "statusDescription": status_description,
            }

            response = self.rpc.put(path=url, payload=payload)
            if response.get("success", False):
                logging.debug("Action status updated successfully")
            else:
                logging.warning(
                    "Failed to update action status: %s",
                    response.get("message", "Unknown error"),
                )

        except Exception as exc:
            logging.error("Exception in update_status: %s", str(exc), exc_info=True)

    def start(self, block: bool = True) -> bool:
        """
        Start the streaming orchestrator.

        This method:
        1. Fetches streaming configuration from API
        2. Creates and configures StreamingGateway
        3. Starts streaming with API status updates
        4. Starts health monitoring

        Args:
            block: Whether to block the thread until the streaming gateway is started (default: True)

        Returns:
            bool: True if started successfully, False otherwise
        """
        with self._state_lock:
            if self._is_running:
                logging.warning("StreamingAction is already running")
                return False

        logging.info("Starting StreamingAction for action: %s", self.action_id)

        try:
            # Update status to starting
            # self.update_status("STARTING", "IN_PROGRESS", "Starting streaming gateway")
            # Fetch input configurations from API
            logging.info("Fetching streaming configuration from API...")
            input_streams = self.gateway_util.get_input_streams()

            if not input_streams:
                if self.allow_empty_start:
                    logging.warning(
                        "No input streams configured - starting with zero cameras. "
                        "Cameras can be added dynamically via event listener."
                    )
                    input_streams = []
                else:
                    raise RuntimeError(
                        "No input streams configured for this streaming gateway"
                    )
            else:
                logging.info("Found %d input streams configured", len(input_streams))

            # Create StreamingGateway with fetched configuration
            logging.info("Creating StreamingGateway instance...")
            self.streaming_gateway = StreamingGateway(
                session=self.session,
                streaming_gateway_id=self.streaming_gateway_id,
                server_id=self.server_id,
                server_type=self.server_type,
                inputs_config=input_streams,
                video_codec=self.video_codec,  # Pass video codec setting
                force_restart=True,  # Always force restart for orchestrator
                enable_event_listening=self.enable_event_listening,  # Enable dynamic event updates
                action_id=self.action_id,  # Pass action_id for API requests
                allow_empty_start=self.allow_empty_start,  # Allow starting with zero cameras
            )

            # Start streaming
            logging.info("Starting streaming gateway...")
            if not self.streaming_gateway.start_streaming():
                raise RuntimeError("Failed to start streaming gateway")

            # Initialize metrics manager
            try:
                logging.info("Initializing metrics manager...")
                metrics_config = MetricsConfig(
                    collection_interval=1.0,  # Collect every second
                    reporting_interval=30.0,  # Report every 30 seconds
                )
                self.metrics_manager = MetricsManager(
                    streaming_gateway=self.streaming_gateway,
                    session=self.session,
                    streaming_gateway_id=self.streaming_gateway_id,
                    action_id=self.action_id,
                    config=metrics_config,
                )
                logging.info("Metrics manager initialized successfully")
            except Exception as exc:
                logging.warning(f"Failed to initialize metrics manager: {exc}", exc_info=True)
                self.metrics_manager = None

            # Mark as running and start monitoring
            with self._state_lock:
                self._is_running = True
                self._stop_event.clear()
                self.stats["start_time"] = time.time()
                self.stats["current_status"] = "running"
                self._restart_attempts = 0

            # Start health monitoring thread
            self._start_monitoring()

            # Initialize and start status listener for stop commands
            try:
                self.status_listener = StreamingStatusListener(
                    session=self.session,
                    streaming_gateway_id=self.streaming_gateway_id,
                    action_id=self.action_id,
                    on_stop_callback=self.stop
                )
                self.status_listener.start()
                logging.info("Status listener started for stop commands")
            except Exception as exc:
                logging.warning(f"Failed to initialize status listener: {exc}", exc_info=True)
                self.status_listener = None

            # Update gateway status to running
            try:
                self.gateway_util.update_status("running")
                logging.info("Gateway status updated to 'running'")
            except Exception as exc:
                logging.warning(f"Failed to update gateway status to running: {exc}")

            logging.info("StreamingAction started successfully")

            if block:
                logging.info("Blocking thread until streaming gateway is started...")
                self._block_thread()

            return True

        except Exception as exc:
            error_msg = f"Failed to start StreamingAction: {str(exc)}"
            logging.error(error_msg, exc_info=True)
            self._record_error(error_msg)
            # self.update_status("STG_ERROR", "FAILED", error_msg)

            # Cleanup on failure
            self._cleanup()
            return False

    def _block_thread(self):
        """Block the thread until the streaming gateway is started."""
        while self._is_running:
            time.sleep(1)

    def stop(self) -> bool:
        """
        Stop the streaming orchestrator.

        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self._state_lock:
            if not self._is_running:
                logging.warning("StreamingAction is not running")
                return False

            logging.info("Stopping StreamingAction...")
            self._is_running = False
            self._stop_event.set()
            self.stats["current_status"] = "stopping"

        try:
            # Update status to stopping
            # self.update_status("STG_STOPPING", "IN_PROGRESS", "Stopping streaming gateway")

            # Stop monitoring thread
            if self._monitor_thread and self._monitor_thread.is_alive():
                logging.info("Waiting for monitor thread to stop...")
                self._monitor_thread.join(timeout=10.0)
                if self._monitor_thread.is_alive():
                    logging.warning("Monitor thread did not stop gracefully")

            # Stop status listener
            if self.status_listener:
                try:
                    logging.info("Stopping status listener...")
                    self.status_listener.stop()
                except Exception as exc:
                    logging.warning(f"Error stopping status listener: {exc}")

            # Stop metrics manager
            if self.metrics_manager:
                try:
                    logging.info("Stopping metrics manager...")
                    self.metrics_manager.stop()
                except Exception as exc:
                    logging.warning(f"Error stopping metrics manager: {exc}")

            # Stop streaming gateway
            if self.streaming_gateway:
                logging.info("Stopping streaming gateway...")
                self.streaming_gateway.stop_streaming()

            # Update total uptime
            if self.stats["start_time"]:
                self.stats["total_uptime"] += time.time() - self.stats["start_time"]

            self.stats["current_status"] = "stopped"
            # self.update_status("STG_STOPPED", "SUCCESS", "Streaming gateway stopped successfully")

            logging.info("StreamingAction stopped successfully")
            return True

        except Exception as exc:
            error_msg = f"Error stopping StreamingAction: {str(exc)}"
            logging.error(error_msg, exc_info=True)
            self._record_error(error_msg)
            # self.update_status("STG_ERROR", "FAILED", error_msg)
            return False

    def restart(self) -> bool:
        """
        Restart the streaming orchestrator.

        Returns:
            bool: True if restarted successfully, False otherwise
        """
        logging.info("Restarting StreamingAction...")

        with self._state_lock:
            self._restart_attempts += 1
            self.stats["restart_count"] += 1
            self.stats["last_restart_time"] = time.time()

        # Update status to restarting
        # self.update_status("STG_RESTARTING", "IN_PROGRESS", f"Restarting streaming gateway (attempt {self._restart_attempts})")

        # Stop current instance
        if self._is_running:
            self.stop()

        # Brief pause before restart
        logging.info("Waiting before restart...")
        time.sleep(2.0)

        # Start again
        return self.start()

    def get_status(self) -> Dict:
        """
        Get current orchestrator status and statistics.

        Returns:
            Dict: Complete status information
        """
        with self._state_lock:
            status = self.stats.copy()
            status["is_running"] = self._is_running
            status["action_id"] = self.action_id
            status["streaming_gateway_id"] = self.streaming_gateway_id
            status["restart_attempts"] = self._restart_attempts

        # Add streaming gateway stats if available
        if self.streaming_gateway:
            try:
                gateway_stats = self.streaming_gateway.get_statistics()
                status["gateway_stats"] = gateway_stats
                logging.debug("Gateway statistics retrieved: %s", gateway_stats)
            except Exception as exc:
                logging.warning(
                    "Failed to get gateway statistics: %s", str(exc), exc_info=True
                )

        return status

    def is_healthy(self) -> bool:
        """
        Check if the orchestrator is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            with self._state_lock:
                if not self._is_running:
                    logging.debug("Health check: not running")
                    return False

            # Check if streaming gateway is healthy
            if not self.streaming_gateway:
                logging.debug("Health check: no streaming gateway")
                return False

            gateway_stats = self.streaming_gateway.get_statistics()
            is_streaming = gateway_stats.get("is_streaming", False)

            logging.debug("Health check: is_streaming=%s", is_streaming)
            return is_streaming

        except Exception as exc:
            logging.warning("Health check failed: %s", str(exc), exc_info=True)
            return False

    def check_action_id_matches(self) -> bool:
        """
        Check if the current action ID matches the streaming gateway's actionRecordID.

        Handles transient errors gracefully:
        - 502 Bad Gateway: Skip check, continue streaming (server temporarily unavailable)
        - 404 Not Found: Stop streaming (gateway may be deleted)
        - Other API errors: Skip check, continue streaming (don't stop on transient issues)

        Returns:
            bool: True if action ID matches or check should be skipped, False if mismatch or gateway deleted
        """
        try:
            self.stats["action_id_checks"] += 1

            # Fetch current streaming gateway details
            gateway_details = self.gateway_util.get_streaming_gateway_by_id()

            # Handle API failures gracefully - don't stop streaming on transient errors
            if gateway_details is None:
                logging.warning(
                    "Action ID check: Failed to fetch gateway details (API returned None), skipping check"
                )
                # Don't increment failure counter - this is expected during transient issues
                return True  # Continue streaming, don't stop on API errors

            gateway_action_id = gateway_details.get("actionRecordID", "")

            # Check if the action IDs match
            if gateway_action_id != self.action_id:
                self.stats["action_id_check_failures"] += 1
                logging.warning(
                    "Action ID mismatch detected! Current action: %s, Gateway actionRecordID: %s",
                    self.action_id,
                    gateway_action_id,
                )
                return False

            logging.debug(
                "Action ID check passed: %s matches gateway actionRecordID",
                self.action_id,
            )
            return True

        except Exception as exc:
            # Unknown error - don't stop streaming on unexpected issues
            logging.warning(
                "Action ID check: Unexpected error '%s', skipping check to avoid false shutdown",
                str(exc)
            )
            return True  # Continue streaming, be conservative

    def _start_monitoring(self):
        """Start the health monitoring thread."""
        self._monitor_thread = threading.Thread(
            target=self._monitor_health,
            daemon=True,
            name=f"StreamingMonitor-{self.streaming_gateway_id}",
        )
        self._monitor_thread.start()
        logging.info(
            "Health monitoring started with interval: %.1f seconds, action ID check interval: %.1f seconds",
            self.monitoring_interval,
            self.action_id_check_interval,
        )

    def _monitor_health(self):
        """Monitor streaming health and handle failures."""
        logging.info("Health monitoring thread started")

        while not self._stop_event.wait(self.monitoring_interval):
            try:
                with self._state_lock:
                    if not self._is_running:
                        logging.debug("Monitor thread exiting: not running")
                        break

                # Check if action ID matches streaming gateway's actionRecordID
                current_time = time.time()
                if (
                    current_time - self._last_action_id_check_time
                    >= self.action_id_check_interval
                ):
                    self._last_action_id_check_time = current_time

                    logging.info("Performing action ID check...")
                    if not self.check_action_id_matches():
                        error_msg = f"Action ID mismatch detected. This action ({self.action_id}) is no longer assigned to this streaming gateway. Stopping..."
                        logging.error(error_msg)
                        self._record_error(error_msg)
                        # self.update_status("STG_ERROR", "FAILED", error_msg)

                        # Stop the streaming action
                        self.stop()
                        break

                self.stats["health_checks"] += 1
                logging.debug(
                    "Performing health check #%d", self.stats["health_checks"]
                )

                if self.is_healthy():
                    # Reset restart attempts on successful health check
                    with self._state_lock:
                        if self._restart_attempts > 0:
                            logging.info(
                                "Health check passed, resetting restart attempts"
                            )
                            self._restart_attempts = 0

                    logging.info("Sending heartbeat to streaming gateway...")

                    # Gather camera configuration data
                    camera_config = self._build_camera_config()

                    # Send heartbeat with camera config
                    self.gateway_util.send_heartbeat(camera_config=camera_config)

                    # Collect and report metrics
                    if self.metrics_manager:
                        try:
                            self.metrics_manager.collect_and_report()
                        except Exception as exc:
                            logging.warning(f"Failed to collect/report metrics: {exc}")
                else:
                    self.stats["health_check_failures"] += 1
                    logging.warning(
                        "Health check failed (failure #%d)",
                        self.stats["health_check_failures"],
                    )

                    if (
                        self.auto_restart
                        and self._restart_attempts < self.max_restart_attempts
                    ):
                        logging.info(
                            "Attempting auto-restart (%d/%d)",
                            self._restart_attempts + 1,
                            self.max_restart_attempts,
                        )

                        # Restart in separate thread to avoid blocking monitor
                        restart_thread = threading.Thread(
                            target=self.restart,
                            daemon=True,
                            name=f"AutoRestart-{self.streaming_gateway_id}",
                        )
                        restart_thread.start()
                        break  # Exit monitoring loop, will be restarted
                    else:
                        error_msg = f"Max restart attempts ({self.max_restart_attempts}) exceeded"
                        logging.error(error_msg, exc_info=True)
                        self._record_error(error_msg)
                        # self.update_status("STG_ERROR", "FAILED", error_msg)
                        break

            except Exception as exc:
                error_msg = f"Error in health monitoring: {str(exc)}"
                logging.error(error_msg, exc_info=True)
                self._record_error(error_msg)

        logging.info("Health monitoring thread ended")

    def _record_error(self, error_msg: str):
        """Record an error in statistics."""
        with self._state_lock:
            self.stats["last_error"] = error_msg
            self.stats["last_error_time"] = time.time()
            logging.error("Error recorded: %s", error_msg, exc_info=True)

    def _build_camera_config(self) -> Dict:
        """
        Build camera configuration data for heartbeat.

        Returns:
            Dict: Camera configuration data including state and settings
        """
        if not self.streaming_gateway:
            return {}

        try:
            # Get full configuration
            config = self.streaming_gateway.get_config()

            # Get runtime statistics
            stats = self.streaming_gateway.get_statistics()

            # Get camera manager stats
            camera_manager_stats = stats.get("camera_manager_stats", {})

            # Build camera config list from inputs_config
            cameras_list = []
            for camera in config.get("inputs_config", []):
                camera_info = {
                    "camera_id": camera.get("camera_id"),
                    "camera_key": camera.get("camera_key"),
                    "camera_group_key": camera.get("camera_group_key"),
                    "camera_location": camera.get("camera_location"),
                    "source": camera.get("source"),
                    "fps": camera.get("fps"),
                    "quality": camera.get("quality"),
                    "width": camera.get("width"),
                    "height": camera.get("height"),
                    "simulate_video_file_stream": camera.get("simulate_video_file_stream", False),
                }
                cameras_list.append(camera_info)

            # Build complete camera config payload
            camera_config = {
                "cameras": cameras_list,
                "stats": {
                    "active_cameras": camera_manager_stats.get("active_cameras", 0),
                    "camera_ids": camera_manager_stats.get("camera_ids", []),
                    "is_streaming": stats.get("is_streaming", False),
                    "runtime_seconds": stats.get("runtime_seconds", 0),
                }
            }

            return camera_config

        except Exception as exc:
            logging.warning(f"Failed to build camera config: {exc}")
            return {}

    def _cleanup(self):
        """Clean up resources."""
        try:
            logging.info("Cleaning up resources...")
            if self.streaming_gateway:
                self.streaming_gateway.stop_streaming()
            logging.info("Cleanup completed")
        except Exception as exc:
            logging.warning("Error during cleanup: %s", str(exc), exc_info=True)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            logging.error("Exception in context manager: %s", exc_val, exc_info=True)
        self.stop()

    def __repr__(self):
        """String representation of the orchestrator."""
        return (
            f"StreamingAction(action_id={self.action_id}, "
            f"gateway_id={self.streaming_gateway_id}, "
            f"status={self.stats.get('current_status', 'unknown')}, "
            f"running={self._is_running})"
        )
