"""Mock stream backend for debugging without Kafka/Redis."""
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class DebugStreamBackend:
    """Mock stream backend that logs messages instead of sending to Kafka/Redis.
    
    This allows testing the full streaming pipeline without actual message brokers.
    Messages can be:
    - Logged to console
    - Saved to JSON files
    - Counted for statistics
    - Inspected for debugging
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        log_messages: bool = True,
        save_frame_data: bool = False
    ):
        """Initialize debug stream backend.
        
        Args:
            output_dir: Directory to save messages (if save_to_files=True)
            save_to_files: Save messages to JSON files
            log_messages: Log message metadata to console
            save_frame_data: Include frame data in saved files (can be large!)
        """
        self.output_dir = Path(output_dir) if output_dir else Path("./debug_stream_output")
        self.save_to_files = save_to_files
        self.log_messages = log_messages
        self.save_frame_data = save_frame_data
        
        if self.save_to_files:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.messages_dir = self.output_dir / "messages"
            self.messages_dir.mkdir(exist_ok=True)
        
        self.message_count = 0
        self.topics = {}
        self.start_time = time.time()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DebugStreamBackend initialized (output_dir={self.output_dir}, save={save_to_files})")
    
    def setup(self, topic: str):
        """Setup a topic (mock operation)."""
        if topic not in self.topics:
            self.topics[topic] = {
                "created_at": datetime.now().isoformat(),
                "message_count": 0
            }
            self.logger.info(f"[DEBUG] Topic setup: {topic}")
    
    def add_message(self, topic_or_channel: str, message: Dict[str, Any], key: Optional[str] = None):
        """Add a message (mock send operation).
        
        Args:
            topic_or_channel: Topic/channel name
            message: Message dictionary
            key: Message key
        """
        self.message_count += 1
        
        if topic_or_channel not in self.topics:
            self.setup(topic_or_channel)
        
        self.topics[topic_or_channel]["message_count"] += 1
        
        # Log message info
        if self.log_messages:
            input_stream = message.get("input_stream", {})
            self.logger.info(
                f"[DEBUG STREAM] Topic: {topic_or_channel}, "
                f"Key: {key}, "
                f"Frame: {input_stream.get('input_order', '?')}, "
                f"Camera: {input_stream.get('camera_info', {}).get('camera_name', '?')}, "
                f"Codec: {input_stream.get('video_codec', '?')}, "
                f"Size: {len(input_stream.get('content', ''))} bytes"
            )
        
        # Save to file
        if self.save_to_files:
            self._save_message_to_file(topic_or_channel, message, key)
    
    def _save_message_to_file(self, topic: str, message: Dict[str, Any], key: Optional[str]):
        """Save message to JSON file."""
        # Remove frame data if requested (to keep files small)
        if not self.save_frame_data and "input_stream" in message:
            message_copy = json.loads(json.dumps(message))  # Deep copy
            if "content" in message_copy["input_stream"]:
                content_size = len(message_copy["input_stream"]["content"])
                message_copy["input_stream"]["content"] = f"<FRAME_DATA_{content_size}_BYTES>"
            message = message_copy
        
        # Create topic directory
        topic_dir = self.messages_dir / topic.replace("/", "_")
        topic_dir.mkdir(exist_ok=True)
        
        # Save message
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"msg_{self.message_count:06d}_{timestamp}.json"
        filepath = topic_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
    
    def close(self):
        """Close backend."""
        runtime = time.time() - self.start_time
        self.logger.info(
            f"[DEBUG] DebugStreamBackend closing: "
            f"{self.message_count} messages sent, "
            f"runtime: {runtime:.1f}s"
        )
        
        # Save summary
        if self.save_to_files:
            summary = {
                "total_messages": self.message_count,
                "runtime_seconds": runtime,
                "topics": self.topics,
                "closed_at": datetime.now().isoformat()
            }
            with open(self.output_dir / "summary.json", 'w') as f:
                json.dump(summary, f, indent=2)
    
    async def async_setup(self, topic: str):
        """Async setup (mock operation)."""
        self.setup(topic)
    
    async def async_add_message(self, topic_or_channel: str, message: Dict[str, Any], key: Optional[str] = None):
        """Async add message (mock operation)."""
        self.add_message(topic_or_channel, message, key)
    
    async def async_close(self):
        """Async close (mock operation)."""
        self.close()
    
    def is_async_setup(self) -> bool:
        """Check if async is setup."""
        return True
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get config (mock)."""
        return {
            'bootstrap_servers': 'debug://localhost:9092',
            'mode': 'debug'
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get stream statistics."""
        return {
            "total_messages": self.message_count,
            "topics": self.topics,
            "runtime_seconds": time.time() - self.start_time
        }

