"""Statistics tracking for streaming."""
import logging
import time
from typing import Dict, Optional, Tuple, Any, List


class StreamStatistics:
    """Manages streaming statistics and timing data."""

    STATS_LOG_INTERVAL = 50
    MAX_HISTORY_SIZE = 1000  # Maximum entries per stream to prevent memory growth

    def __init__(self):
        """Initialize statistics tracker."""
        self.frames_sent = 0
        self.frames_skipped = 0
        self.frames_diff_sent = 0
        self.bytes_saved = 0

        # Per-stream timing data - keeping for backward compatibility
        self.last_read_times: Dict[str, float] = {}
        self.last_write_times: Dict[str, float] = {}
        self.last_process_times: Dict[str, float] = {}

        # Per-stream frame size tracking (ACG frame size)
        self.last_frame_sizes: Dict[str, int] = {}

        # History storage for accurate statistics (accumulated between reporting intervals)
        # These are bounded to MAX_HISTORY_SIZE entries per stream
        self.read_times_history: Dict[str, List[float]] = {}
        self.write_times_history: Dict[str, List[float]] = {}
        self.process_times_history: Dict[str, List[float]] = {}
        self.frame_sizes_history: Dict[str, List[int]] = {}
        self.frame_timestamps_history: Dict[str, List[float]] = {}
        self.encoding_times_history: Dict[str, List[float]] = {}  # NEW: encoding time tracking

        # Per-stream input order tracking
        self.input_order: Dict[str, int] = {}

        self.logger = logging.getLogger(__name__)
    
    def increment_frames_sent(self):
        """Increment sent frames counter."""
        self.frames_sent += 1
    
    def increment_frames_skipped(self):
        """Increment skipped frames counter."""
        self.frames_skipped += 1
    
    def increment_frames_diff_sent(self):
        """Increment diff frames counter."""
        self.frames_diff_sent += 1
    
    def add_bytes_saved(self, bytes_count: int):
        """Add to bytes saved counter."""
        self.bytes_saved += bytes_count
    
    def update_timing(
        self,
        stream_key: str,
        read_time: float,
        write_time: float,
        process_time: float,
        frame_size: Optional[int] = None,
        encoding_time: float = 0.0
    ):
        """Update timing statistics for a stream.

        Args:
            stream_key: Stream identifier
            read_time: Time spent reading frame
            write_time: Time spent writing/sending frame
            process_time: Total processing time
            frame_size: Size of encoded frame in bytes (ACG frame size)
            encoding_time: Time spent encoding frame (NEW)
        """
        key = self._normalize_key(stream_key)
        timestamp = time.time()

        # Update last values (for backward compatibility)
        self.last_read_times[key] = read_time
        self.last_write_times[key] = write_time
        self.last_process_times[key] = process_time
        if frame_size is not None:
            self.last_frame_sizes[key] = frame_size

        # Append to history for accurate statistics (bounded to prevent memory growth)
        if key not in self.read_times_history:
            self.read_times_history[key] = []
            self.write_times_history[key] = []
            self.process_times_history[key] = []
            self.frame_sizes_history[key] = []
            self.frame_timestamps_history[key] = []
            self.encoding_times_history[key] = []

        self.read_times_history[key].append(read_time)
        self.write_times_history[key].append(write_time)
        self.process_times_history[key].append(process_time)
        self.frame_timestamps_history[key].append(timestamp)
        self.encoding_times_history[key].append(encoding_time)

        if frame_size is not None:
            self.frame_sizes_history[key].append(frame_size)

        # Enforce size limits to prevent unbounded growth
        # Keep only the last MAX_HISTORY_SIZE entries
        if len(self.read_times_history[key]) > self.MAX_HISTORY_SIZE:
            self.read_times_history[key] = self.read_times_history[key][-self.MAX_HISTORY_SIZE:]
            self.write_times_history[key] = self.write_times_history[key][-self.MAX_HISTORY_SIZE:]
            self.process_times_history[key] = self.process_times_history[key][-self.MAX_HISTORY_SIZE:]
            self.frame_timestamps_history[key] = self.frame_timestamps_history[key][-self.MAX_HISTORY_SIZE:]
            self.encoding_times_history[key] = self.encoding_times_history[key][-self.MAX_HISTORY_SIZE:]
            if len(self.frame_sizes_history[key]) > self.MAX_HISTORY_SIZE:
                self.frame_sizes_history[key] = self.frame_sizes_history[key][-self.MAX_HISTORY_SIZE:]
    
    def get_timing(self, stream_key: str) -> Tuple[float, float, float]:
        """Get timing data for a stream.
        
        Args:
            stream_key: Stream identifier
            
        Returns:
            Tuple of (read_time, write_time, process_time)
        """
        key = self._normalize_key(stream_key)
        return (
            self.last_read_times.get(key, 0.0),
            self.last_write_times.get(key, 0.0),
            self.last_process_times.get(key, 0.0)
        )
    
    def get_next_input_order(self, stream_key: str) -> int:
        """Get next input order number for a stream.
        
        Args:
            stream_key: Stream identifier
            
        Returns:
            Next input order number
        """
        key = self._normalize_key(stream_key)
        if key not in self.input_order:
            self.input_order[key] = 0
        self.input_order[key] += 1
        return self.input_order[key]
    
    def should_log_stats(self) -> bool:
        """Check if it's time to log statistics.
        
        Returns:
            True if should log stats based on interval
        """
        return self.frames_sent % self.STATS_LOG_INTERVAL == 0
    
    def log_periodic_stats(
        self,
        stream_key: str,
        read_time: float,
        encoding_time: float,
        write_time: float
    ):
        """Log periodic statistics.

        Args:
            stream_key: Stream identifier
            read_time: Time spent reading frame
            encoding_time: Time spent encoding frame
            write_time: Time spent writing frame
        """
        if self.should_log_stats():
            total = self.frames_sent + self.frames_skipped + self.frames_diff_sent
            self.logger.info(
                f"Stream [{stream_key}]: {self.frames_sent} sent, "
                f"{self.frames_skipped} skipped, {self.frames_diff_sent} diff | "
                f"Timing: read={read_time*1000:.1f}ms, encode={encoding_time*1000:.1f}ms, "
                f"write={write_time*1000:.1f}ms"
            )

    def log_detailed_stats(self, stream_key: str) -> None:
        """Log comprehensive metrics for a stream.

        Args:
            stream_key: Stream identifier
        """
        stats = self.get_timing_statistics(stream_key)
        if not stats:
            return

        # Calculate additional metrics
        total_frames = self.frames_sent + self.frames_skipped + self.frames_diff_sent
        skip_rate = (self.frames_skipped / total_frames * 100) if total_frames > 0 else 0

        # FPS metrics
        fps_stats = stats.get("fps", {})
        fps_current = fps_stats.get("avg", 0)
        fps_min = fps_stats.get("min", 0)
        fps_max = fps_stats.get("max", 0)

        # Latency breakdown (ms)
        read_ms = stats.get("read_time_ms", {}).get("avg", 0)
        encoding_ms = stats.get("encoding_time_ms", {}).get("avg", 0)
        write_ms = stats.get("write_time_ms", {}).get("avg", 0)
        process_ms = stats.get("process_time_ms", {}).get("avg", 0)

        # Frame size stats (KB)
        frame_size_stats = stats.get("frame_size_bytes", {})
        frame_size_avg_kb = frame_size_stats.get("avg", 0) / 1024
        frame_size_min_kb = frame_size_stats.get("min", 0) / 1024
        frame_size_max_kb = frame_size_stats.get("max", 0) / 1024

        # Throughput (KB/s)
        throughput_kbps = (frame_size_avg_kb * fps_current) if fps_current > 0 else 0

        self.logger.info(
            f"Stream Metrics [{stream_key}]: "
            f"FPS={fps_current:.1f} (min={fps_min:.1f}, max={fps_max:.1f}) | "
            f"Latency: read={read_ms:.1f}ms, encode={encoding_ms:.1f}ms, write={write_ms:.1f}ms, total={process_ms:.1f}ms | "
            f"Frames: sent={self.frames_sent}, skipped={self.frames_skipped} ({skip_rate:.1f}%) | "
            f"Frame size: {frame_size_avg_kb:.1f}KB (min={frame_size_min_kb:.1f}, max={frame_size_max_kb:.1f}) | "
            f"Throughput: {throughput_kbps:.1f} KB/s"
        )

    def log_aggregated_stats(self) -> None:
        """Log aggregated metrics across all streams."""
        total_frames_sent = self.frames_sent
        total_frames_skipped = self.frames_skipped
        total_frames_diff = self.frames_diff_sent
        total_frames = total_frames_sent + total_frames_skipped + total_frames_diff

        if total_frames == 0:
            return

        skip_rate = (total_frames_skipped / total_frames * 100)
        diff_rate = (total_frames_diff / total_frames * 100)

        # Aggregate FPS across all streams
        all_fps = []
        for stream_key in self.last_read_times.keys():
            stats = self.get_timing_statistics(stream_key)
            if stats and "fps" in stats:
                fps_avg = stats["fps"].get("avg", 0)
                if fps_avg > 0:
                    all_fps.append(fps_avg)

        avg_fps = sum(all_fps) / len(all_fps) if all_fps else 0

        self.logger.info(
            f"Gateway Aggregate Metrics: "
            f"Total frames: {total_frames} (sent={total_frames_sent}, skipped={total_frames_skipped}, diff={total_frames_diff}) | "
            f"Skip rate: {skip_rate:.1f}%, Diff rate: {diff_rate:.1f}% | "
            f"Avg FPS across {len(all_fps)} streams: {avg_fps:.1f}"
        )

    def get_transmission_stats(self, video_codec: str, active_streams: int) -> Dict[str, Any]:
        """Get comprehensive transmission statistics.
        
        Args:
            video_codec: Current video codec being used
            active_streams: Number of active streams
            
        Returns:
            Dictionary with all transmission statistics
        """
        total = self.frames_sent + self.frames_skipped + self.frames_diff_sent
        return {
            "frames_sent_full": self.frames_sent,
            "frames_skipped": self.frames_skipped,
            "frames_diff_sent": self.frames_diff_sent,
            "total_frames_processed": total,
            "skip_rate": (self.frames_skipped / total) if total > 0 else 0.0,
            "diff_rate": (self.frames_diff_sent / total) if total > 0 else 0.0,
            "full_rate": (self.frames_sent / total) if total > 0 else 0.0,
            "bytes_saved": self.bytes_saved,
            "video_codec": video_codec,
            "active_streams": active_streams,
        }
    
    def get_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get timing statistics for streams.

        Args:
            stream_key: Specific stream key, or None for all streams

        Returns:
            Dictionary with timing statistics
        """
        if stream_key is None:
            return {
                "per_stream": {
                    sk: {
                        "last_read_time_sec": self.last_read_times.get(sk, 0),
                        "last_write_time_sec": self.last_write_times.get(sk, 0),
                        "last_process_time_sec": self.last_process_times.get(sk, 0),
                        "last_frame_size_bytes": self.last_frame_sizes.get(sk, 0),
                    }
                    for sk in self.last_read_times.keys()
                },
                "active_streams": list(self.last_read_times.keys()),
            }
        else:
            read, write, process = self.get_timing(stream_key)
            key = self._normalize_key(stream_key)
            return {
                "stream_key": stream_key,
                "last_read_time_sec": read,
                "last_write_time_sec": write,
                "last_process_time_sec": process,
                "last_frame_size_bytes": self.last_frame_sizes.get(key, 0),
            }

    def get_timing_statistics(self, stream_key: str) -> Dict[str, Any]:
        """Calculate min/max/avg statistics from accumulated timing history.

        Args:
            stream_key: Stream identifier

        Returns:
            Dictionary with statistical metrics for read_time, write_time, process_time,
            frame_size, and FPS calculations
        """
        key = self._normalize_key(stream_key)

        # Initialize result structure
        result = {
            "read_time_ms": {"min": 0, "max": 0, "avg": 0, "count": 0},
            "write_time_ms": {"min": 0, "max": 0, "avg": 0, "count": 0},
            "encoding_time_ms": {"min": 0, "max": 0, "avg": 0, "count": 0},  # NEW
            "process_time_ms": {"min": 0, "max": 0, "avg": 0, "count": 0},
            "frame_size_bytes": {"min": 0, "max": 0, "avg": 0, "count": 0},
            "fps": {"min": 0, "max": 0, "avg": 0},
        }

        # Calculate read time statistics
        if key in self.read_times_history and self.read_times_history[key]:
            read_times = self.read_times_history[key]
            result["read_time_ms"] = {
                "min": min(read_times) * 1000,  # Convert to ms
                "max": max(read_times) * 1000,
                "avg": (sum(read_times) / len(read_times)) * 1000,
                "count": len(read_times),
            }

        # Calculate write time statistics
        if key in self.write_times_history and self.write_times_history[key]:
            write_times = self.write_times_history[key]
            result["write_time_ms"] = {
                "min": min(write_times) * 1000,
                "max": max(write_times) * 1000,
                "avg": (sum(write_times) / len(write_times)) * 1000,
                "count": len(write_times),
            }

        # Calculate process time statistics
        if key in self.process_times_history and self.process_times_history[key]:
            process_times = self.process_times_history[key]
            result["process_time_ms"] = {
                "min": min(process_times) * 1000,
                "max": max(process_times) * 1000,
                "avg": (sum(process_times) / len(process_times)) * 1000,
                "count": len(process_times),
            }

        # Calculate encoding time statistics
        if key in self.encoding_times_history and self.encoding_times_history[key]:
            encoding_times = self.encoding_times_history[key]
            result["encoding_time_ms"] = {
                "min": min(encoding_times) * 1000,
                "max": max(encoding_times) * 1000,
                "avg": (sum(encoding_times) / len(encoding_times)) * 1000,
                "count": len(encoding_times),
            }

        # Calculate frame size statistics
        if key in self.frame_sizes_history and self.frame_sizes_history[key]:
            frame_sizes = self.frame_sizes_history[key]
            result["frame_size_bytes"] = {
                "min": min(frame_sizes),
                "max": max(frame_sizes),
                "avg": sum(frame_sizes) / len(frame_sizes),
                "count": len(frame_sizes),
            }

        # Calculate FPS statistics from timestamps
        if key in self.frame_timestamps_history and len(self.frame_timestamps_history[key]) >= 2:
            timestamps = self.frame_timestamps_history[key]

            # Calculate instantaneous FPS between consecutive frames
            fps_values = []
            for i in range(1, len(timestamps)):
                time_diff = timestamps[i] - timestamps[i - 1]
                if time_diff > 0:
                    fps_values.append(1.0 / time_diff)

            if fps_values:
                result["fps"] = {
                    "min": min(fps_values),
                    "max": max(fps_values),
                    "avg": sum(fps_values) / len(fps_values),
                }
            else:
                # Fallback: calculate average FPS over entire period
                total_time = timestamps[-1] - timestamps[0]
                if total_time > 0:
                    avg_fps = (len(timestamps) - 1) / total_time
                    result["fps"] = {"min": avg_fps, "max": avg_fps, "avg": avg_fps}

        return result

    def clear_timing_history(self, stream_key: Optional[str] = None):
        """Clear accumulated timing history for a stream or all streams.

        This should be called after metrics have been reported to prevent
        unbounded memory growth.

        Args:
            stream_key: Specific stream key to clear, or None to clear all streams
        """
        if stream_key is None:
            # Clear all streams
            self.read_times_history.clear()
            self.write_times_history.clear()
            self.process_times_history.clear()
            self.frame_sizes_history.clear()
            self.frame_timestamps_history.clear()
            self.encoding_times_history.clear()
            self.logger.debug("Cleared timing history for all streams")
        else:
            # Clear specific stream
            key = self._normalize_key(stream_key)
            if key in self.read_times_history:
                self.read_times_history[key].clear()
            if key in self.write_times_history:
                self.write_times_history[key].clear()
            if key in self.process_times_history:
                self.process_times_history[key].clear()
            if key in self.frame_sizes_history:
                self.frame_sizes_history[key].clear()
            if key in self.frame_timestamps_history:
                self.frame_timestamps_history[key].clear()
            if key in self.encoding_times_history:
                self.encoding_times_history[key].clear()
            self.logger.debug(f"Cleared timing history for stream: {stream_key}")
    
    def reset(self):
        """Reset all statistics."""
        self.frames_sent = 0
        self.frames_skipped = 0
        self.frames_diff_sent = 0
        self.bytes_saved = 0
        self.last_read_times.clear()
        self.last_write_times.clear()
        self.last_process_times.clear()
        self.last_frame_sizes.clear()
        # Clear history as well
        self.clear_timing_history()
        self.logger.info("Reset transmission statistics")
    
    def _normalize_key(self, stream_key: Optional[str]) -> str:
        """Normalize stream key to handle None values."""
        return stream_key if stream_key is not None else "default"

