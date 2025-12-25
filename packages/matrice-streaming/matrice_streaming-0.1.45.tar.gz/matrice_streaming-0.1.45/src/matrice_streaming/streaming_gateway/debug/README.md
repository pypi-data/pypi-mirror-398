# Debug Streaming Gateway

A complete debugging and testing framework for the streaming gateway that works **without any external dependencies** - no Kafka, Redis, or API required!

## 🎯 Purpose

The debug module allows you to:

- ✅ **Test locally** - No servers or network required
- ✅ **Debug encoding** - Test H.264, H.265 frame, and H.265 stream modes
- ✅ **Inspect messages** - Save all streamed messages to JSON files
- ✅ **Measure performance** - Get detailed timing and throughput statistics
- ✅ **CI/CD friendly** - Perfect for automated testing pipelines
- ✅ **Rapid development** - Iterate quickly without infrastructure setup

## 📦 What's Included

### Core Components

| Component | Description |
|-----------|-------------|
| `DebugStreamingGateway` | Main gateway for testing with local videos |
| `DebugStreamingAction` | Simplified action runner for testing |
| `DebugStreamBackend` | Mock Kafka/Redis that logs messages |
| `MockSession` | Mock authentication session |
| `MockRPC` | Mock API client with fake responses |

### Features

- 🎥 **Stream local video files** - Any format supported by OpenCV
- 🔄 **Loop videos** - Continuous streaming for long-term tests
- 📊 **Rich statistics** - Frame counts, timing, throughput
- 💾 **Message capture** - Save messages to JSON for inspection
- 🔧 **Full codec support** - Test all encoding modes
- 📐 **Custom resolution** - Override video dimensions
- 🎛️ **Configurable** - Control FPS, quality, hardware acceleration

## 🚀 Quick Start

### Basic Usage

```python
from matrice_streaming.streaming_gateway.debug import DebugStreamingGateway

# Create gateway with your video file
gateway = DebugStreamingGateway(
    video_paths=["my_video.mp4"],
    fps=10,
    video_codec="h265-frame",
    loop_videos=True
)

# Start streaming
gateway.start_streaming()

# Let it run
import time
time.sleep(30)

# Check stats
stats = gateway.get_statistics()
print(f"Frames sent: {stats['transmission_stats']['frames_sent_full']}")

# Stop
gateway.stop_streaming()
```

### Multiple Videos

```python
# Stream multiple videos simultaneously
gateway = DebugStreamingGateway(
    video_paths=[
        "video1.mp4",
        "video2.mp4",
        "video3.mp4"
    ],
    fps=10,
    video_codec="h265-frame"
)

gateway.start_streaming()
```

### Save Messages to Files

```python
# Save all streamed messages for inspection
gateway = DebugStreamingGateway(
    video_paths=["video.mp4"],
    fps=5,
    save_to_files=True,
    output_dir="./my_debug_output",
    save_frame_data=False  # Exclude large frame data
)

gateway.start_streaming()
time.sleep(30)
gateway.stop_streaming()

# Check output:
# ./my_debug_output/messages/ - Individual message JSON files
# ./my_debug_output/summary.json - Overall summary
```

### Using DebugStreamingAction

```python
from matrice_streaming.streaming_gateway.debug import DebugStreamingAction

# Simpler API for quick tests
action = DebugStreamingAction(
    video_paths=["video.mp4"],
    fps=10,
    video_codec="h265-frame",
    save_to_files=True
)

action.start()
time.sleep(20)
print(action.get_status())
action.stop()
```

### Context Manager

```python
# Automatic cleanup
with DebugStreamingGateway(
    video_paths=["video.mp4"],
    fps=10
) as gateway:
    gateway.start_streaming()
    time.sleep(30)
    # Automatic stop on exit
```

## 📖 Complete Examples

See `example_debug_streaming.py` for comprehensive examples:

```bash
python example_debug_streaming.py
```

Examples include:
1. Basic single video streaming
2. Multiple video streams
3. Saving messages to files
4. Using DebugStreamingAction
5. Testing different codecs and resolutions

## 🔧 Configuration Options

### DebugStreamingGateway Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_paths` | List[str] | **Required** | Paths to video files |
| `fps` | int | 10 | Frames per second to stream |
| `video_codec` | str | "h265-frame" | Codec: h264, h265-frame, h265-chunk |
| `h265_quality` | int | 23 | H.265 CRF (0-51, lower=better) |
| `use_hardware` | bool | False | Use hardware encoding if available |
| `loop_videos` | bool | True | Loop videos continuously |
| `output_dir` | str | "./debug_stream_output" | Output directory |
| `save_to_files` | bool | False | Save messages to JSON files |
| `log_messages` | bool | True | Log message metadata to console |
| `save_frame_data` | bool | False | Include frame data in saved files |
| `width` | int | None | Override video width |
| `height` | int | None | Override video height |

## 📊 Statistics and Monitoring

### Get Real-Time Statistics

```python
stats = gateway.get_statistics()

print(f"Running: {stats['is_streaming']}")
print(f"Runtime: {stats['runtime_seconds']:.1f}s")
print(f"Frames sent: {stats['transmission_stats']['frames_sent_full']}")
print(f"Messages: {stats['backend_stats']['total_messages']}")
print(f"Active streams: {stats['transmission_stats']['active_streams']}")
```

### Get Timing Statistics

```python
# Per-stream timing
timing = gateway.get_timing_stats("Debug_Camera_1")
print(f"Read time: {timing['last_read_time_sec']*1000:.1f}ms")
print(f"Write time: {timing['last_write_time_sec']*1000:.1f}ms")

# All streams
all_timing = gateway.get_timing_stats()
for stream, times in all_timing['per_stream'].items():
    print(f"{stream}: {times}")
```

## 🧪 Testing Different Codecs

```python
codecs = ["h264", "h265-frame", "h265-chunk"]

for codec in codecs:
    print(f"\nTesting {codec}...")
    
    gateway = DebugStreamingGateway(
        video_paths=["video.mp4"],
        fps=10,
        video_codec=codec,
        loop_videos=False
    )
    
    gateway.start_streaming()
    time.sleep(10)
    
    stats = gateway.get_statistics()
    print(f"Frames: {stats['transmission_stats']['frames_sent_full']}")
    
    gateway.stop_streaming()
```

## 📝 Output Files

When `save_to_files=True`:

```
output_dir/
├── messages/
│   └── debug_input_topic_0/
│       ├── msg_000001_20250112_143022_123456.json
│       ├── msg_000002_20250112_143022_234567.json
│       └── ...
└── summary.json
```

### Message JSON Structure

```json
{
  "frame_id": "abc123...",
  "input_name": "frame_1",
  "input_unit": "frame",
  "input_stream": {
    "camera_info": {
      "camera_name": "Debug_Camera_1",
      "location": "Debug_Location"
    },
    "video_codec": "h265",
    "encoding_type": "h265_frame",
    "stream_fps": 10,
    "original_fps": 30.0,
    "content": "<FRAME_DATA_12345_BYTES>",
    "latency_stats": {
      "last_read_time_sec": 0.023,
      "last_write_time_sec": 0.001
    }
  }
}
```

### Summary JSON

```json
{
  "total_messages": 150,
  "runtime_seconds": 15.2,
  "topics": {
    "debug_input_topic_0": {
      "created_at": "2025-01-12T14:30:22",
      "message_count": 150
    }
  },
  "closed_at": "2025-01-12T14:30:37"
}
```

## 🎓 Use Cases

### 1. Local Development

Test your streaming logic without setting up infrastructure:

```python
gateway = DebugStreamingGateway(
    video_paths=["test_video.mp4"],
    fps=30,
    log_messages=True
)
gateway.start_streaming(block=True)
```

### 2. CI/CD Pipeline

Automated testing in CI:

```python
import pytest

def test_streaming_pipeline():
    gateway = DebugStreamingGateway(
        video_paths=["test_fixture.mp4"],
        fps=10,
        loop_videos=False
    )
    
    gateway.start_streaming()
    time.sleep(10)
    stats = gateway.get_statistics()
    gateway.stop_streaming()
    
    assert stats['transmission_stats']['frames_sent_full'] > 0
    assert stats['is_streaming'] == False
```

### 3. Performance Testing

Measure encoding performance:

```python
import time

gateway = DebugStreamingGateway(
    video_paths=["4k_video.mp4"],
    fps=30,
    video_codec="h265-frame",
    width=3840,
    height=2160
)

start = time.time()
gateway.start_streaming()
time.sleep(60)
gateway.stop_streaming()

stats = gateway.get_statistics()
fps_actual = stats['transmission_stats']['frames_sent_full'] / (time.time() - start)
print(f"Actual FPS: {fps_actual:.2f}")
```

### 4. Codec Comparison

Compare different encoding modes:

```python
def benchmark_codec(codec):
    gateway = DebugStreamingGateway(
        video_paths=["benchmark.mp4"],
        video_codec=codec,
        fps=30,
        loop_videos=False
    )
    
    start = time.time()
    gateway.start_streaming()
    
    # Wait for completion
    while gateway.is_streaming:
        time.sleep(0.1)
    
    elapsed = time.time() - start
    stats = gateway.get_statistics()
    
    return {
        "codec": codec,
        "frames": stats['transmission_stats']['frames_sent_full'],
        "time": elapsed,
        "fps": stats['transmission_stats']['frames_sent_full'] / elapsed
    }

results = [benchmark_codec(c) for c in ["h264", "h265-frame", "h265-chunk"]]
for r in results:
    print(f"{r['codec']}: {r['fps']:.2f} FPS")
```

## 🔍 Debugging Tips

### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

gateway = DebugStreamingGateway(...)
```

### Inspect Specific Messages

```python
# Save messages
gateway = DebugStreamingGateway(
    video_paths=["video.mp4"],
    save_to_files=True,
    save_frame_data=True  # Include frame data
)

gateway.start_streaming()
time.sleep(5)
gateway.stop_streaming()

# Manually inspect saved JSON files
```

### Monitor Encoding Performance

```python
gateway.start_streaming()

for i in range(10):
    time.sleep(1)
    timing = gateway.get_timing_stats()
    print(f"Encode time: {timing['last_process_time_sec']*1000:.1f}ms")
```

## ⚠️ Limitations

The debug mode is for **testing only**:

- ❌ No actual Kafka/Redis connectivity
- ❌ No real API authentication
- ❌ Messages are logged/saved, not sent to brokers
- ❌ No distributed streaming

For production use, use the regular `StreamingGateway` and `StreamingAction` classes.

## 🆘 Troubleshooting

### Video Not Found

```python
from pathlib import Path

video_path = "video.mp4"
if not Path(video_path).exists():
    print(f"Video not found: {video_path}")
    print(f"Current directory: {Path.cwd()}")
```

### No Frames Sent

Check video can be opened:

```python
import cv2

cap = cv2.VideoCapture("video.mp4")
if not cap.isOpened():
    print("Cannot open video file")
else:
    ret, frame = cap.read()
    if ret:
        print(f"Video OK: {frame.shape}")
    cap.release()
```

### Low FPS

The debug backend is synchronous. For high FPS testing, use lower resolution:

```python
gateway = DebugStreamingGateway(
    video_paths=["video.mp4"],
    fps=60,
    width=320,  # Lower resolution
    height=240
)
```

## 📚 See Also

- `example_debug_streaming.py` - Complete working examples
- Main `CameraStreamer` class - Production streaming
- `StreamingGateway` - Real gateway with Kafka/Redis
- `StreamingAction` - Production action runner

## 💡 Tips

1. **Start small** - Test with one low-res video first
2. **Save selectively** - Use `save_frame_data=False` to keep file sizes small
3. **Monitor stats** - Check statistics regularly to catch issues
4. **Test codecs** - Compare performance of different encoding modes
5. **Use context managers** - Ensures proper cleanup

Happy debugging! 🐛✨

