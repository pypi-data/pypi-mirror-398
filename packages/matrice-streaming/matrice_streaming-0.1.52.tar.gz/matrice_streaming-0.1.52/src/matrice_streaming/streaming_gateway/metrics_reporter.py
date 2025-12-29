"""
Streaming Gateway Metrics Collection and Reporting System.

This module provides comprehensive metrics collection for streaming gateways,
including per-camera throughput and latency statistics, with reporting via Kafka.
"""

import base64
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kafka import KafkaProducer


@dataclass
class MetricsConfig:
    """Configuration for metrics collection and reporting."""

    # Collection and reporting intervals
    collection_interval: float = 1.0  # Collect metrics every second
    reporting_interval: float = 30.0  # Report aggregated metrics every 30 seconds
    history_window: int = 30  # Keep 30 seconds of history for statistics
    log_interval: float = 300.0  # Log metrics sends every 5 minutes

    # Kafka configuration
    metrics_topic: str = "streaming_gateway_metrics"
    kafka_timeout: float = 5.0  # Timeout for Kafka operations

    # Statistics configuration
    calculate_percentiles: bool = True
    percentiles: List[int] = field(default_factory=lambda: [0, 50, 100])


class MetricsCalculator:
    """Calculate statistical metrics over time windows."""

    @staticmethod
    def calculate_statistics(values: List[float]) -> Dict[str, float]:
        """
        Calculate min, max, avg, p0, p50, p100 from a list of values.

        Args:
            values: List of numeric values

        Returns:
            Dictionary with statistical metrics
        """
        if not values:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p0": 0.0,
                "p50": 0.0,
                "p100": 0.0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(values) / count,
            "p0": sorted_values[0],  # Minimum
            "p50": sorted_values[count // 2],  # Median
            "p100": sorted_values[-1],  # Maximum
        }

    @staticmethod
    def calculate_fps(frame_count_start: int, frame_count_end: int, time_elapsed: float) -> float:
        """
        Calculate frames per second.

        Args:
            frame_count_start: Starting frame count
            frame_count_end: Ending frame count
            time_elapsed: Time elapsed in seconds

        Returns:
            Frames per second
        """
        if time_elapsed <= 0:
            return 0.0

        frame_diff = frame_count_end - frame_count_start
        return frame_diff / time_elapsed


class MetricsCollector:
    """Collects and aggregates streaming gateway metrics."""

    def __init__(self, streaming_gateway, config: MetricsConfig):
        """
        Initialize metrics collector.

        Args:
            streaming_gateway: StreamingGateway instance
            config: Metrics configuration
        """
        self.streaming_gateway = streaming_gateway
        self.config = config

        # Thread safety
        self._lock = threading.RLock()

        # Time-series history
        self.metrics_history: List[Dict[str, Any]] = []

        # Track frame counts for FPS calculation
        self.camera_frame_counts: Dict[str, List[tuple]] = {}  # camera_id -> [(timestamp, count)]

        # Track which flow is being used
        self.use_async_workers = getattr(streaming_gateway, 'use_async_workers', False)

    def collect_snapshot(self) -> Dict[str, Any]:
        """
        Collect current metrics snapshot from streaming gateway.

        Returns:
            Dictionary containing current metrics state
        """
        with self._lock:
            try:
                # Get overall statistics from streaming gateway
                gateway_stats = self.streaming_gateway.get_statistics()

                # Route to appropriate collection method based on flow
                if self.use_async_workers:
                    return self._collect_async_worker_snapshot(gateway_stats)
                else:
                    return self._collect_camera_streamer_snapshot(gateway_stats)

            except Exception as e:
                logging.error(f"Error collecting metrics snapshot: {e}", exc_info=True)
                return None

    def _collect_camera_streamer_snapshot(self, gateway_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect metrics from original CameraStreamer flow."""
        # Get camera streamer for detailed metrics
        camera_streamer = self.streaming_gateway.camera_streamer
        if not camera_streamer:
            return None

        # Collect per-camera metrics
        camera_metrics = {}

        # Get active stream keys
        stream_keys = gateway_stats.get("my_stream_keys", [])

        for stream_key in stream_keys:
            # Get timing statistics for this stream
            timing = camera_streamer.statistics.get_timing_stats(stream_key)

            if timing:
                # Get camera_id from the streaming gateway mapping
                camera_id = self.streaming_gateway.get_camera_id_for_stream_key(stream_key)
                if not camera_id:
                    # Fallback: try to extract from stream_key if mapping not available
                    camera_id = stream_key.split('_')[0] if '_' in stream_key else stream_key

                camera_metrics[camera_id] = {
                    "stream_key": stream_key,
                    "read_time": timing.get("last_read_time_sec", 0.0),  # Camera reading latency
                    "write_time": timing.get("last_write_time_sec", 0.0),  # Gateway sending latency
                    "process_time": timing.get("last_process_time_sec", 0.0),  # Total processing time
                    "frame_size": timing.get("last_frame_size_bytes", 0),  # ACG frame size in bytes
                }

        # Get transmission stats for frame counts
        transmission_stats = gateway_stats.get("transmission_stats", {})

        snapshot = {
            "timestamp": time.time(),
            "cameras": camera_metrics,
            "frames_sent": transmission_stats.get("frames_sent_full", 0),
            "total_frames_processed": transmission_stats.get("total_frames_processed", 0),
            "flow_type": "camera_streamer",
        }

        return snapshot

    def _collect_async_worker_snapshot(self, gateway_stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect metrics from new async worker flow."""
        worker_manager = self.streaming_gateway.worker_manager
        if not worker_manager:
            return None

        # Collect per-camera metrics from worker statistics
        camera_metrics = {}

        # Get active stream keys
        stream_keys = gateway_stats.get("my_stream_keys", [])

        # Get worker statistics
        worker_stats = gateway_stats.get("worker_stats", {})
        health_reports = worker_stats.get("health_reports", {})

        for stream_key in stream_keys:
            # Get camera_id from the streaming gateway mapping
            camera_id = self.streaming_gateway.get_camera_id_for_stream_key(stream_key)
            if not camera_id:
                camera_id = stream_key.split('_')[0] if '_' in stream_key else stream_key

            # For async workers, we track basic info (detailed timing not yet available)
            camera_metrics[camera_id] = {
                "stream_key": stream_key,
                "read_time": 0.0,  # Not tracked per-camera in async flow yet
                "write_time": 0.0,  # Not tracked per-camera in async flow yet
                "process_time": 0.0,  # Not tracked per-camera in async flow yet
                "frame_size": 0,  # Not tracked per-camera in async flow yet
            }

        # Calculate aggregate stats from worker health reports
        total_cameras = worker_stats.get("total_cameras", len(stream_keys))
        running_workers = worker_stats.get("running_workers", 0)

        snapshot = {
            "timestamp": time.time(),
            "cameras": camera_metrics,
            "frames_sent": 0,  # Not tracked in async flow yet
            "total_frames_processed": 0,  # Not tracked in async flow yet
            "flow_type": "async_workers",
            "worker_stats": {
                "num_workers": worker_stats.get("num_workers", 0),
                "running_workers": running_workers,
                "total_cameras": total_cameras,
            },
        }

        return snapshot

    def add_to_history(self, snapshot: Dict[str, Any]):
        """
        Add snapshot to rolling history window.

        Args:
            snapshot: Metrics snapshot to add
        """
        if not snapshot:
            return

        with self._lock:
            self.metrics_history.append(snapshot)

            # Prune old data outside the window
            cutoff_time = time.time() - self.config.history_window
            self.metrics_history = [
                m for m in self.metrics_history
                if m["timestamp"] > cutoff_time
            ]

    def get_aggregated_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Calculate aggregated metrics from accumulated timing history.

        Returns:
            Dictionary with aggregated per-camera metrics
        """
        with self._lock:
            if not self.metrics_history:
                return None

            try:
                # Route to appropriate aggregation method based on flow
                if self.use_async_workers:
                    return self._get_async_worker_aggregated_metrics()
                else:
                    return self._get_camera_streamer_aggregated_metrics()

            except Exception as e:
                logging.error(f"Error calculating aggregated metrics: {e}", exc_info=True)
                return None

    def _get_camera_streamer_aggregated_metrics(self) -> Optional[List[Dict[str, Any]]]:
        """Get aggregated metrics for CameraStreamer flow."""
        # Get camera streamer for accessing timing statistics
        camera_streamer = self.streaming_gateway.camera_streamer
        if not camera_streamer:
            return None

        # Get active stream keys from the most recent snapshot
        stream_keys = set()
        for snapshot in self.metrics_history:
            for camera_id, metrics in snapshot.get("cameras", {}).items():
                stream_keys.add(metrics.get("stream_key"))

        # Calculate statistics for each stream using accumulated history
        per_camera_metrics = []

        for stream_key in stream_keys:
            if not stream_key:
                continue

            # Get real statistics from accumulated timing history
            stats = camera_streamer.statistics.get_timing_statistics(stream_key)

            if not stats:
                continue

            # Get camera_id from the streaming gateway mapping
            camera_id = self.streaming_gateway.get_camera_id_for_stream_key(stream_key)
            if not camera_id:
                # Fallback: try to extract from stream_key if mapping not available
                camera_id = stream_key.split('_')[0] if '_' in stream_key else stream_key

            # Get read time statistics (already in milliseconds)
            read_time_ms = stats.get("read_time_ms", {})
            read_stats = {
                "min": read_time_ms.get("min", 0.0),
                "max": read_time_ms.get("max", 0.0),
                "avg": read_time_ms.get("avg", 0.0),
                "p0": read_time_ms.get("min", 0.0),
                "p50": read_time_ms.get("avg", 0.0),  # Use avg as approximation for median
                "p100": read_time_ms.get("max", 0.0),
                "unit": "ms"
            }

            # Get write time statistics (already in milliseconds)
            write_time_ms = stats.get("write_time_ms", {})
            write_stats = {
                "min": write_time_ms.get("min", 0.0),
                "max": write_time_ms.get("max", 0.0),
                "avg": write_time_ms.get("avg", 0.0),
                "p0": write_time_ms.get("min", 0.0),
                "p50": write_time_ms.get("avg", 0.0),
                "p100": write_time_ms.get("max", 0.0),
                "unit": "ms"
            }

            # Get FPS statistics (real calculations from timestamps)
            fps_data = stats.get("fps", {})
            fps_stats = {
                "min": fps_data.get("min", 0.0),
                "max": fps_data.get("max", 0.0),
                "avg": fps_data.get("avg", 0.0),
                "p0": fps_data.get("min", 0.0),
                "p50": fps_data.get("avg", 0.0),
                "p100": fps_data.get("max", 0.0),
                "unit": "fps"
            }

            # Get frame size statistics
            frame_size_data = stats.get("frame_size_bytes", {})
            frame_size_stats = {
                "min": frame_size_data.get("min", 0.0),
                "max": frame_size_data.get("max", 0.0),
                "avg": frame_size_data.get("avg", 0.0),
                "p0": frame_size_data.get("min", 0.0),
                "p50": frame_size_data.get("avg", 0.0),
                "p100": frame_size_data.get("max", 0.0),
                "unit": "bytes"
            }

            # Build camera metrics in the required format
            camera_metric = {
                "camera_id": camera_id,
                "camera_reading": {
                    "throughput": fps_stats,
                    "latency": read_stats
                },
                "gateway_sending": {
                    "throughput": fps_stats,  # Same as camera reading
                    "latency": write_stats
                },
                "frame_size_stats": frame_size_stats
            }

            per_camera_metrics.append(camera_metric)

        return per_camera_metrics

    def _get_async_worker_aggregated_metrics(self) -> Optional[List[Dict[str, Any]]]:
        """Get aggregated metrics for async worker flow."""
        worker_manager = self.streaming_gateway.worker_manager
        if not worker_manager:
            return None

        # Get active stream keys from the most recent snapshot
        stream_keys = set()
        for snapshot in self.metrics_history:
            for camera_id, metrics in snapshot.get("cameras", {}).items():
                stream_keys.add(metrics.get("stream_key"))

        # Get worker statistics (includes per_camera_stats from health reports)
        gateway_stats = self.streaming_gateway.get_statistics()
        worker_stats = gateway_stats.get("worker_stats", {})
        per_camera_stats = worker_stats.get("per_camera_stats", {})

        # Build per-camera metrics using real stats from workers
        per_camera_metrics = []

        for stream_key in stream_keys:
            if not stream_key:
                continue

            # Get camera_id from the streaming gateway mapping
            camera_id = self.streaming_gateway.get_camera_id_for_stream_key(stream_key)
            if not camera_id:
                camera_id = stream_key.split('_')[0] if '_' in stream_key else stream_key

            # Get real stats from worker health reports if available
            camera_stats = per_camera_stats.get(stream_key, {})

            # Build FPS stats from worker data
            fps_data = camera_stats.get('fps', {})
            fps_stats = {
                "min": fps_data.get("min", 0.0),
                "max": fps_data.get("max", 0.0),
                "avg": fps_data.get("avg", 0.0),
                "p0": fps_data.get("min", 0.0),
                "p50": fps_data.get("avg", 0.0),
                "p100": fps_data.get("max", 0.0),
                "unit": "fps"
            }

            # Build read latency stats (already in ms from worker)
            read_time_ms = camera_stats.get('read_time_ms', {})
            read_stats = {
                "min": read_time_ms.get("min", 0.0),
                "max": read_time_ms.get("max", 0.0),
                "avg": read_time_ms.get("avg", 0.0),
                "p0": read_time_ms.get("min", 0.0),
                "p50": read_time_ms.get("avg", 0.0),
                "p100": read_time_ms.get("max", 0.0),
                "unit": "ms"
            }

            # Build write latency stats (already in ms from worker)
            write_time_ms = camera_stats.get('write_time_ms', {})
            write_stats = {
                "min": write_time_ms.get("min", 0.0),
                "max": write_time_ms.get("max", 0.0),
                "avg": write_time_ms.get("avg", 0.0),
                "p0": write_time_ms.get("min", 0.0),
                "p50": write_time_ms.get("avg", 0.0),
                "p100": write_time_ms.get("max", 0.0),
                "unit": "ms"
            }

            # Build frame size stats (in bytes from worker)
            frame_size_data = camera_stats.get('frame_size_bytes', {})
            frame_size_stats = {
                "min": frame_size_data.get("min", 0.0),
                "max": frame_size_data.get("max", 0.0),
                "avg": frame_size_data.get("avg", 0.0),
                "p0": frame_size_data.get("min", 0.0),
                "p50": frame_size_data.get("avg", 0.0),
                "p100": frame_size_data.get("max", 0.0),
                "unit": "bytes"
            }

            # Build camera metrics with real data
            camera_metric = {
                "camera_id": camera_id,
                "camera_reading": {
                    "throughput": fps_stats,
                    "latency": read_stats
                },
                "gateway_sending": {
                    "throughput": fps_stats,  # Same throughput for gateway sending
                    "latency": write_stats
                },
                "frame_size_stats": frame_size_stats,
                "flow_type": "async_workers"
            }

            per_camera_metrics.append(camera_metric)

        return per_camera_metrics


class MetricsReporter:
    """Sends metrics to Kafka topic."""

    def __init__(self, session, streaming_gateway_id: str, config: MetricsConfig):
        """
        Initialize metrics reporter.

        Args:
            session: Session object for API calls
            streaming_gateway_id: ID of the streaming gateway
            config: Metrics configuration
        """
        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.config = config

        self.producer: Optional[KafkaProducer] = None
        self._init_kafka_producer()

    def _init_kafka_producer(self):
        """Initialize Kafka producer for metrics."""
        try:
            # Get Kafka configuration (same pattern as EventListener)
            response = self.session.rpc.get("/v1/actions/get_kafka_info")

            if not response or "data" not in response:
                logging.error("Failed to get Kafka info for metrics reporter")
                return

            data = response.get("data", {})

            # Decode connection info
            ip = base64.b64decode(data["ip"]).decode("utf-8")
            port = base64.b64decode(data["port"]).decode("utf-8")
            bootstrap_servers = f"{ip}:{port}"

            # Create Kafka producer config
            kafka_config = {
                'bootstrap_servers': bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 1,  # Wait for leader acknowledgment
                'retries': 3,
                'max_in_flight_requests_per_connection': 1,
            }

            # Add SASL authentication if available
            if "username" in data and "password" in data:
                username = base64.b64decode(data["username"]).decode("utf-8")
                password = base64.b64decode(data["password"]).decode("utf-8")

                kafka_config.update({
                    'security_protocol': 'SASL_PLAINTEXT',
                    'sasl_mechanism': 'SCRAM-SHA-256',
                    'sasl_plain_username': username,
                    'sasl_plain_password': password,
                })

            # Create producer
            self.producer = KafkaProducer(**kafka_config)
            logging.info(f"Kafka metrics producer initialized: {bootstrap_servers}")

        except Exception as e:
            logging.error(f"Failed to initialize Kafka metrics producer: {e}", exc_info=True)
            self.producer = None

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """
        Send metrics to Kafka topic.

        Args:
            metrics: Metrics payload to send

        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logging.warning("Kafka producer not initialized, cannot send metrics")
            return False

        try:
            # Send to Kafka
            future = self.producer.send(
                self.config.metrics_topic,
                value=metrics,
                key=self.streaming_gateway_id
            )

            # Wait for send to complete with timeout
            future.get(timeout=self.config.kafka_timeout)

            # Logging is handled by MetricsManager to avoid excessive logs
            return True

        except Exception as e:
            logging.error(f"Failed to send metrics to Kafka: {e}", exc_info=True)
            return False

    def close(self):
        """Close Kafka producer."""
        if self.producer:
            try:
                self.producer.close(timeout=5)
                logging.info("Kafka metrics producer closed")
            except Exception as e:
                logging.error(f"Error closing Kafka producer: {e}")


class HeartbeatReporter:
    """Sends heartbeat messages to Kafka topic."""

    def __init__(self, session, streaming_gateway_id: str, topic: str = "streaming_gateway_heartbeat", kafka_timeout: float = 5.0):
        """
        Initialize heartbeat reporter.

        Args:
            session: Session object for API calls
            streaming_gateway_id: ID of the streaming gateway
            topic: Kafka topic to send heartbeats to (default: streaming_gateway_heartbeat)
            kafka_timeout: Timeout for Kafka operations
        """
        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.topic = topic
        self.kafka_timeout = kafka_timeout

        self.producer: Optional[KafkaProducer] = None
        self._init_kafka_producer()

    def _init_kafka_producer(self):
        """Initialize Kafka producer for heartbeats."""
        try:
            # Get Kafka configuration (same pattern as EventListener)
            response = self.session.rpc.get("/v1/actions/get_kafka_info")

            if not response or "data" not in response:
                logging.error("Failed to get Kafka info for heartbeat reporter")
                return

            data = response.get("data", {})

            # Decode connection info
            ip = base64.b64decode(data["ip"]).decode("utf-8")
            port = base64.b64decode(data["port"]).decode("utf-8")
            bootstrap_servers = f"{ip}:{port}"

            # Create Kafka producer config
            kafka_config = {
                'bootstrap_servers': bootstrap_servers,
                'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 1,  # Wait for leader acknowledgment
                'retries': 3,
                'max_in_flight_requests_per_connection': 1,
            }

            # Add SASL authentication if available
            if "username" in data and "password" in data:
                username = base64.b64decode(data["username"]).decode("utf-8")
                password = base64.b64decode(data["password"]).decode("utf-8")

                kafka_config.update({
                    'security_protocol': 'SASL_PLAINTEXT',
                    'sasl_mechanism': 'SCRAM-SHA-256',
                    'sasl_plain_username': username,
                    'sasl_plain_password': password,
                })

            # Create producer
            self.producer = KafkaProducer(**kafka_config)
            logging.info(f"Kafka heartbeat producer initialized: {bootstrap_servers}, topic: {self.topic}")

        except Exception as e:
            logging.error(f"Failed to initialize Kafka heartbeat producer: {e}", exc_info=True)
            self.producer = None

    def send_heartbeat(self, camera_config: Dict[str, Any]) -> bool:
        """
        Send heartbeat to Kafka topic.

        Args:
            camera_config: Camera configuration payload to send

        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logging.warning("Kafka producer not initialized, cannot send heartbeat")
            return False

        try:
            # Build heartbeat message with cameraConfig wrapper
            heartbeat = {
                "streaming_gateway_id": self.streaming_gateway_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "cameraConfig": camera_config
            }

            # Send to Kafka
            future = self.producer.send(
                self.topic,
                value=heartbeat,
                key=self.streaming_gateway_id
            )

            # Wait for send to complete with timeout
            future.get(timeout=self.kafka_timeout)

            logging.info(f"Heartbeat sent to Kafka topic '{self.topic}' with {len(camera_config.get('cameras', []))} cameras")
            return True

        except Exception as e:
            logging.error(f"Failed to send heartbeat to Kafka: {e}", exc_info=True)
            return False

    def close(self):
        """Close Kafka producer."""
        if self.producer:
            try:
                self.producer.close(timeout=5)
                logging.info("Kafka heartbeat producer closed")
            except Exception as e:
                logging.error(f"Error closing Kafka heartbeat producer: {e}")


class MetricsManager:
    """
    Main orchestrator for metrics collection and reporting.

    This class coordinates the collection of metrics from the streaming gateway,
    calculates statistics, and reports them via Kafka.
    """

    # ANSI escape codes for BOLD text in terminal
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def __init__(
        self,
        streaming_gateway,
        session,
        streaming_gateway_id: str,
        action_id: Optional[str] = None,
        config: Optional[MetricsConfig] = None
    ):
        """
        Initialize metrics manager.

        Args:
            streaming_gateway: StreamingGateway instance
            session: Session object for API calls
            streaming_gateway_id: ID of the streaming gateway
            action_id: Optional action ID
            config: Optional metrics configuration (uses default if not provided)
        """
        self.streaming_gateway = streaming_gateway
        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.action_id = action_id
        self.config = config or MetricsConfig()

        # Initialize components
        self.collector = MetricsCollector(streaming_gateway, self.config)
        self.reporter = MetricsReporter(session, streaming_gateway_id, self.config)

        # Track which flow is being used
        self.use_async_workers = getattr(streaming_gateway, 'use_async_workers', False)

        # Tracking
        self.last_report_time = 0
        self.last_log_time = 0
        self.last_metrics_log_time = 0
        self.metrics_log_interval = 60.0  # Log metrics summary every 60 seconds
        self.last_aggregate_log_time = 0
        self.aggregate_log_interval = 60.0  # Log aggregate metrics with BOLD every 60 seconds
        self.enabled = True

        flow_type = "async_workers" if self.use_async_workers else "camera_streamer"
        logging.info(f"Metrics manager initialized (flow: {flow_type})")

    def collect_and_report(self):
        """
        Collect current metrics and report if interval has elapsed.

        This method should be called periodically (e.g., every 1-30 seconds)
        from the health monitoring loop.
        """
        if not self.enabled:
            return

        try:
            # Always collect current snapshot
            snapshot = self.collector.collect_snapshot()
            if snapshot:
                self.collector.add_to_history(snapshot)

            current_time = time.time()

            # Log metrics summary periodically
            if current_time - self.last_metrics_log_time >= self.metrics_log_interval:
                self._log_metrics_summary(snapshot)
                self.last_metrics_log_time = current_time

            # Log aggregate metrics with BOLD every minute
            if current_time - self.last_aggregate_log_time >= self.aggregate_log_interval:
                self._log_aggregate_metrics_bold()
                self.last_aggregate_log_time = current_time

            # Report if interval has elapsed
            if current_time - self.last_report_time >= self.config.reporting_interval:
                self._generate_and_send_report()
                self.last_report_time = current_time

        except Exception as e:
            logging.error(f"Error in metrics collect_and_report: {e}", exc_info=True)

    def _log_metrics_summary(self, snapshot: Optional[Dict[str, Any]]):
        """Log a summary of current metrics to console."""
        try:
            gateway_stats = self.streaming_gateway.get_statistics()

            if self.use_async_workers:
                self._log_async_worker_metrics(gateway_stats, snapshot)
            else:
                self._log_camera_streamer_metrics(gateway_stats, snapshot)

        except Exception as e:
            logging.warning(f"Error logging metrics summary: {e}")

    def _log_aggregate_metrics_bold(self):
        """Log comprehensive aggregate metrics with BOLD formatting every minute.

        Reports:
        - Overall AVG FPS across all cameras
        - Latency breakdown (read, encode/convert, write averages)
        - Total throughput (sum of all cameras' FPS)
        - Total data throughput (KB/s)
        """
        try:
            gateway_stats = self.streaming_gateway.get_statistics()

            if self.use_async_workers:
                self._log_aggregate_async_workers_bold(gateway_stats)
            else:
                self._log_aggregate_camera_streamer_bold(gateway_stats)

        except Exception as e:
            logging.warning(f"Error logging aggregate metrics: {e}")

    def _log_aggregate_async_workers_bold(self, gateway_stats: Dict[str, Any]):
        """Log aggregate metrics for async workers with BOLD formatting."""
        worker_stats = gateway_stats.get("worker_stats", {})
        stream_keys = gateway_stats.get("my_stream_keys", [])
        runtime = gateway_stats.get("runtime_seconds", 0)

        num_workers = worker_stats.get("num_workers", 0)
        running_workers = worker_stats.get("running_workers", 0)
        total_cameras = worker_stats.get("total_cameras", len(stream_keys))
        per_camera_stats = worker_stats.get("per_camera_stats", {})

        # Detect SHM mode from worker_manager
        use_shm = False
        shm_format = "N/A"
        worker_manager = getattr(self.streaming_gateway, 'worker_manager', None)
        if worker_manager:
            use_shm = getattr(worker_manager, 'use_shm', False)
            shm_format = getattr(worker_manager, 'shm_frame_format', 'N/A') if use_shm else "N/A"

        # Aggregate FPS stats
        total_fps = 0.0
        fps_values = []
        for stream_key, stats in per_camera_stats.items():
            fps_avg = stats.get("fps", {}).get("avg", 0)
            if fps_avg > 0:
                total_fps += fps_avg
                fps_values.append(fps_avg)

        avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
        min_fps = min(fps_values) if fps_values else 0
        max_fps = max(fps_values) if fps_values else 0

        # Aggregate latency stats (in ms)
        read_times = []
        write_times = []
        encoding_times = []

        for stream_key, stats in per_camera_stats.items():
            read_ms = stats.get("read_time_ms", {}).get("avg", 0)
            write_ms = stats.get("write_time_ms", {}).get("avg", 0)
            encoding_ms = stats.get("encoding_time_ms", {}).get("avg", 0)

            if read_ms > 0:
                read_times.append(read_ms)
            if write_ms > 0:
                write_times.append(write_ms)
            if encoding_ms > 0:
                encoding_times.append(encoding_ms)

        avg_read_ms = sum(read_times) / len(read_times) if read_times else 0
        avg_write_ms = sum(write_times) / len(write_times) if write_times else 0
        avg_encoding_ms = sum(encoding_times) / len(encoding_times) if encoding_times else 0
        total_latency_ms = avg_read_ms + avg_encoding_ms + avg_write_ms

        # Aggregate frame size and throughput
        total_frame_size_kb = 0.0
        frame_sizes = []
        for stream_key, stats in per_camera_stats.items():
            frame_size_bytes = stats.get("frame_size_bytes", {}).get("avg", 0)
            if frame_size_bytes > 0:
                frame_sizes.append(frame_size_bytes)
                total_frame_size_kb += frame_size_bytes / 1024

        avg_frame_size_kb = (sum(frame_sizes) / len(frame_sizes) / 1024) if frame_sizes else 0

        # Total throughput: sum of (FPS * frame_size) across all cameras = total KB/s
        total_throughput_kbps = 0.0
        for stream_key, stats in per_camera_stats.items():
            fps_avg = stats.get("fps", {}).get("avg", 0)
            frame_size_bytes = stats.get("frame_size_bytes", {}).get("avg", 0)
            if fps_avg > 0 and frame_size_bytes > 0:
                total_throughput_kbps += (fps_avg * frame_size_bytes) / 1024

        total_throughput_mbps = total_throughput_kbps / 1024

        # Log with BOLD formatting
        B = self.BOLD
        R = self.RESET

        # Mode indicator
        mode_str = f"SHM ({shm_format})" if use_shm else "JPEG"
        encode_label = "Convert" if use_shm else "Encode"

        logging.info(
            f"\n{B}{'='*80}{R}\n"
            f"{B}[STREAMING GATEWAY AGGREGATE METRICS - 1 MIN SUMMARY]{R}\n"
            f"{B}{'='*80}{R}\n"
            f"{B}Mode:{R} {mode_str} | "
            f"{B}Workers:{R} {running_workers}/{num_workers} active | "
            f"{B}Cameras:{R} {total_cameras} streaming | "
            f"{B}Runtime:{R} {runtime:.0f}s\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}FPS:{R} avg={avg_fps:.1f} | min={min_fps:.1f} | max={max_fps:.1f} | "
            f"{B}TOTAL={total_fps:.1f} fps{R}\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}LATENCY BREAKDOWN:{R}\n"
            f"  • Read:     {avg_read_ms:.2f} ms (avg)\n"
            f"  • {encode_label}:   {avg_encoding_ms:.2f} ms (avg)\n"
            f"  • Write:    {avg_write_ms:.2f} ms (avg)\n"
            f"  • {B}TOTAL:    {total_latency_ms:.2f} ms{R}\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}THROUGHPUT:{R}\n"
            f"  • Avg Frame Size: {avg_frame_size_kb:.1f} KB\n"
            f"  • {B}TOTAL: {total_throughput_mbps:.2f} MB/s ({total_throughput_kbps:.1f} KB/s){R}\n"
            f"{B}{'='*80}{R}"
        )

    def _log_aggregate_camera_streamer_bold(self, gateway_stats: Dict[str, Any]):
        """Log aggregate metrics for CameraStreamer with BOLD formatting."""
        camera_streamer = self.streaming_gateway.camera_streamer
        if not camera_streamer:
            return

        stream_keys = gateway_stats.get("my_stream_keys", [])
        transmission_stats = gateway_stats.get("transmission_stats", {})
        runtime = gateway_stats.get("runtime_seconds", 0)

        # Aggregate FPS stats
        fps_values = []
        read_times = []
        write_times = []
        encoding_times = []
        frame_sizes = []

        # Calculate total throughput properly per-camera
        total_throughput_kbps = 0.0

        for stream_key in stream_keys:
            timing_stats = camera_streamer.statistics.get_timing_statistics(stream_key)
            if timing_stats:
                fps_avg = timing_stats.get("fps", {}).get("avg", 0)
                if fps_avg > 0:
                    fps_values.append(fps_avg)

                read_ms = timing_stats.get("read_time_ms", {}).get("avg", 0)
                write_ms = timing_stats.get("write_time_ms", {}).get("avg", 0)
                encoding_ms = timing_stats.get("encoding_time_ms", {}).get("avg", 0)
                frame_size_bytes = timing_stats.get("frame_size_bytes", {}).get("avg", 0)

                if read_ms > 0:
                    read_times.append(read_ms)
                if write_ms > 0:
                    write_times.append(write_ms)
                if encoding_ms > 0:
                    encoding_times.append(encoding_ms)
                if frame_size_bytes > 0:
                    frame_sizes.append(frame_size_bytes)

                # Calculate throughput per camera (FPS * frame_size)
                if fps_avg > 0 and frame_size_bytes > 0:
                    total_throughput_kbps += (fps_avg * frame_size_bytes) / 1024

        total_fps = sum(fps_values)
        avg_fps = sum(fps_values) / len(fps_values) if fps_values else 0
        min_fps = min(fps_values) if fps_values else 0
        max_fps = max(fps_values) if fps_values else 0

        avg_read_ms = sum(read_times) / len(read_times) if read_times else 0
        avg_write_ms = sum(write_times) / len(write_times) if write_times else 0
        avg_encoding_ms = sum(encoding_times) / len(encoding_times) if encoding_times else 0
        total_latency_ms = avg_read_ms + avg_encoding_ms + avg_write_ms

        avg_frame_size_kb = (sum(frame_sizes) / len(frame_sizes) / 1024) if frame_sizes else 0

        total_throughput_mbps = total_throughput_kbps / 1024

        frames_sent = transmission_stats.get("frames_sent_full", 0)
        frames_skipped = transmission_stats.get("frames_skipped", 0)

        # Log with BOLD formatting
        B = self.BOLD
        R = self.RESET

        logging.info(
            f"\n{B}{'='*80}{R}\n"
            f"{B}[STREAMING GATEWAY AGGREGATE METRICS - 1 MIN SUMMARY]{R}\n"
            f"{B}{'='*80}{R}\n"
            f"{B}Cameras:{R} {len(stream_keys)} streaming | "
            f"{B}Runtime:{R} {runtime:.0f}s | "
            f"{B}Frames:{R} sent={frames_sent}, skipped={frames_skipped}\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}FPS:{R} avg={avg_fps:.1f} | min={min_fps:.1f} | max={max_fps:.1f} | "
            f"{B}TOTAL={total_fps:.1f} fps{R}\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}LATENCY BREAKDOWN:{R}\n"
            f"  • Read:     {avg_read_ms:.2f} ms (avg)\n"
            f"  • Encode:   {avg_encoding_ms:.2f} ms (avg)\n"
            f"  • Write:    {avg_write_ms:.2f} ms (avg)\n"
            f"  • {B}TOTAL:    {total_latency_ms:.2f} ms{R}\n"
            f"{B}{'─'*80}{R}\n"
            f"{B}THROUGHPUT:{R}\n"
            f"  • Avg Frame Size: {avg_frame_size_kb:.1f} KB\n"
            f"  • {B}TOTAL: {total_throughput_mbps:.2f} MB/s ({total_throughput_kbps:.1f} KB/s){R}\n"
            f"{B}{'='*80}{R}"
        )

    def _log_camera_streamer_metrics(self, gateway_stats: Dict[str, Any], snapshot: Optional[Dict[str, Any]]):
        """Log metrics summary for CameraStreamer flow."""
        camera_streamer = self.streaming_gateway.camera_streamer
        if not camera_streamer:
            return

        stream_keys = gateway_stats.get("my_stream_keys", [])
        transmission_stats = gateway_stats.get("transmission_stats", {})
        runtime = gateway_stats.get("runtime_seconds", 0)

        # Build per-camera summary with frame size
        camera_summaries = []
        total_frame_size_kb = 0
        camera_count_with_size = 0
        
        for stream_key in stream_keys[:5]:  # Limit to first 5 cameras for log brevity
            timing_stats = camera_streamer.statistics.get_timing_statistics(stream_key)
            if timing_stats:
                read_ms = timing_stats.get("read_time_ms", {}).get("avg", 0.0)
                write_ms = timing_stats.get("write_time_ms", {}).get("avg", 0.0)
                frame_size_bytes = timing_stats.get("frame_size_bytes", {}).get("avg", 0)
                frame_kb = frame_size_bytes / 1024
                camera_summaries.append(f"{stream_key}(r:{read_ms:.1f}ms,w:{write_ms:.1f}ms,{frame_kb:.1f}KB)")
                
                if frame_size_bytes > 0:
                    total_frame_size_kb += frame_kb
                    camera_count_with_size += 1

        # Calculate average frame size across all cameras
        avg_frame_size_kb = total_frame_size_kb / camera_count_with_size if camera_count_with_size > 0 else 0

        frames_sent = transmission_stats.get("frames_sent_full", 0)
        avg_fps = frames_sent / runtime if runtime > 0 else 0

        logging.info(
            f"[METRICS] CameraStreamer | "
            f"cameras={len(stream_keys)} | "
            f"frames_sent={frames_sent} | "
            f"avg_fps={avg_fps:.1f} | "
            f"avg_frame_size={avg_frame_size_kb:.1f}KB | "
            f"runtime={runtime:.0f}s | "
            f"samples: {', '.join(camera_summaries[:3])}"
        )

    def _log_async_worker_metrics(self, gateway_stats: Dict[str, Any], snapshot: Optional[Dict[str, Any]]):
        """Log metrics summary for async worker flow."""
        worker_stats = gateway_stats.get("worker_stats", {})
        stream_keys = gateway_stats.get("my_stream_keys", [])
        runtime = gateway_stats.get("runtime_seconds", 0)

        num_workers = worker_stats.get("num_workers", 0)
        running_workers = worker_stats.get("running_workers", 0)
        total_cameras = worker_stats.get("total_cameras", len(stream_keys))
        worker_camera_counts = worker_stats.get("worker_camera_counts", {})
        health_reports = worker_stats.get("health_reports", {})
        per_camera_stats = worker_stats.get("per_camera_stats", {})

        # Build worker load summary
        worker_loads = []
        for worker_id, count in worker_camera_counts.items():
            health = health_reports.get(worker_id, {})
            status = health.get("status", "unknown")
            worker_loads.append(f"W{worker_id}:{count}({status})")

        # Calculate average frame size across all cameras
        total_frame_size_kb = 0
        camera_count_with_size = 0
        for stream_key, stats in per_camera_stats.items():
            frame_size_bytes = stats.get("frame_size_bytes", {}).get("avg", 0)
            if frame_size_bytes > 0:
                total_frame_size_kb += frame_size_bytes / 1024
                camera_count_with_size += 1
        
        avg_frame_size_kb = total_frame_size_kb / camera_count_with_size if camera_count_with_size > 0 else 0

        # Calculate average FPS across all cameras
        total_fps = 0
        camera_count_with_fps = 0
        for stream_key, stats in per_camera_stats.items():
            fps_avg = stats.get("fps", {}).get("avg", 0)
            if fps_avg > 0:
                total_fps += fps_avg
                camera_count_with_fps += 1
        
        avg_fps = total_fps / camera_count_with_fps if camera_count_with_fps > 0 else 0

        logging.info(
            f"[METRICS] AsyncWorkers | "
            f"workers={running_workers}/{num_workers} | "
            f"cameras={total_cameras} | "
            f"avg_fps={avg_fps:.1f} | "
            f"avg_frame_size={avg_frame_size_kb:.1f}KB | "
            f"runtime={runtime:.0f}s | "
            f"distribution: {', '.join(worker_loads[:4])}"
        )

    def _generate_and_send_report(self):
        """Generate metrics report and send to Kafka."""
        try:
            # Get aggregated metrics
            per_camera_metrics = self.collector.get_aggregated_metrics()

            if not per_camera_metrics:
                logging.debug("No metrics data available for reporting")
                return

            # Build report in the required format
            flow_type = "async_workers" if self.use_async_workers else "camera_streamer"
            report = {
                "streaming_gateway_id": self.streaming_gateway_id,
                "action_id": self.action_id or "unknown",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "per_camera_metrics": per_camera_metrics,
                "flow_type": flow_type
            }

            # Send report
            success = self.reporter.send_metrics(report)

            # Check if we should log (every 5 minutes)
            current_time = time.time()
            should_log = (current_time - self.last_log_time >= self.config.log_interval)

            if success:
                if should_log:
                    logging.info(f"Metrics report sent successfully ({len(per_camera_metrics)} cameras, flow={flow_type})")
                    self.last_log_time = current_time

                # Clear timing history after successful reporting to prevent unbounded memory growth
                # Only applicable for CameraStreamer flow
                if not self.use_async_workers:
                    camera_streamer = self.streaming_gateway.camera_streamer
                    if camera_streamer and hasattr(camera_streamer, 'statistics'):
                        camera_streamer.statistics.clear_timing_history()
                        if should_log:
                            logging.debug("Cleared timing history after successful metrics reporting")
            else:
                if should_log:
                    logging.warning(f"Failed to send metrics report (flow={flow_type})")
                    self.last_log_time = current_time

        except Exception as e:
            logging.error(f"Error generating/sending metrics report: {e}", exc_info=True)

    def stop(self):
        """Stop metrics collection and close resources."""
        self.enabled = False
        self.reporter.close()
        logging.info("Metrics manager stopped")
