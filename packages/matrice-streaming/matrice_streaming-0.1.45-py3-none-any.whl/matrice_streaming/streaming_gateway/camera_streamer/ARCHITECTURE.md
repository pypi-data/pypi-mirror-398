# Camera Streamer Architecture

## Overview

The `CameraStreamer` has been completely refactored into a modular, maintainable architecture with clear separation of concerns. The main class is now **simple and focused**, delegating specific responsibilities to specialized helper classes.

## Key Improvements

### ✅ **Modular Design**
- Each component has a single, well-defined responsibility
- Easy to test, maintain, and extend
- Clear interfaces between components

### ✅ **Robust Retry Logic**
- **Never gives up** - infinite retry with exponential backoff
- Automatic reconnection on failures
- Smart failure detection and handling

### ✅ **Simplified Main Class**
- Main `CameraStreamer` class reduced from ~999 lines to ~550 lines
- Clear public API
- Orchestrates components without implementation details

---

## Architecture Components

### 1. **CameraStreamer** (Main Orchestrator)
**File:** `camera_streamer.py` (~550 lines)

**Responsibilities:**
- Public API for streaming operations
- Orchestrates all helper components
- Manages streaming threads
- Topic registration and setup

**Key Methods:**
- `start_stream()` - Blocking stream
- `start_background_stream()` - Non-blocking stream
- `stop_streaming()` - Stop all streams
- `produce_request()` - Direct message production

---

### 2. **VideoCaptureManager**
**File:** `video_capture_manager.py`

**Responsibilities:**
- Opening video captures (camera, file, RTSP, HTTP)
- Downloading and caching remote video files
- Detecting source types
- Configuring capture settings
- Extracting video properties

**Key Methods:**
- `prepare_source()` - Download URLs if needed
- `open_capture()` - Open with retry logic
- `get_video_properties()` - Extract FPS, resolution, etc.
- `calculate_frame_skip()` - For RTSP streams
- `cleanup()` - Remove temp files

---

### 3. **EncoderManager**
**File:** `encoder_manager.py`

**Responsibilities:**
- Managing H.265 frame encoders
- Managing H.265 stream encoders
- Encoding frames with proper fallback
- Encoder lifecycle management

**Key Methods:**
- `encode_frame()` - Encode using configured mode
- `cleanup()` - Close all encoders

**Modes:**
- **Frame mode:** Each frame encoded independently
- **Stream mode:** Continuous stream encoding with chunking

---

### 4. **StreamStatistics**
**File:** `stream_statistics.py`

**Responsibilities:**
- Tracking frame counts (sent, skipped, diff)
- Timing statistics per stream
- Input order tracking
- Periodic logging
- Statistics reporting

**Key Methods:**
- `increment_frames_sent()` / `skipped()` / `diff_sent()`
- `update_timing()` - Record read/write/process times
- `get_next_input_order()` - Get sequence number
- `log_periodic_stats()` - Automatic logging
- `get_transmission_stats()` - Get full report
- `reset()` - Reset all counters

---

### 5. **StreamMessageBuilder**
**File:** `message_builder.py`

**Responsibilities:**
- Building frame metadata
- Constructing complete stream messages
- Message serialization
- Timestamp generation

**Key Methods:**
- `build_frame_metadata()` - Create metadata dict
- `build_message()` - Create complete message
- Helper methods for timestamps, formats

---

### 6. **RetryManager**
**File:** `retry_manager.py`

**Responsibilities:**
- Managing retry cycles
- Tracking consecutive failures
- Exponential backoff calculation
- **Infinite retry logic** - never gives up!

**Key Methods:**
- `should_reconnect()` - Check if too many failures
- `record_read_failure()` / `record_success()`
- `handle_connection_failure()` - Log and track
- `wait_before_retry()` - Exponential backoff
- `handle_successful_reconnect()` - Reset counters

**Retry Behavior:**
- Max 10 consecutive read failures before reconnect
- Exponential backoff: 5s → 30s (capped)
- **Retries forever** - no maximum retry limit!

---

### 7. **FrameProcessor**
**File:** `frame_processor.py`

**Responsibilities:**
- Frame resizing
- Frame skip logic
- Dimension calculations

**Key Methods:**
- `resize_frame()` - Resize if needed
- `should_skip_frame()` - Check skip rate
- `calculate_actual_dimensions()` - Compute output size

---

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    CameraStreamer                        │
│                  (Main Orchestrator)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌────────────────┐
│ VideoCap     │ │ Encoder  │ │ RetryManager   │
│ Manager      │ │ Manager  │ │ (Never Quits)  │
└──────────────┘ └──────────┘ └────────────────┘
        │              │              │
        │              ▼              │
        │      ┌──────────────┐      │
        │      │ Statistics   │      │
        │      └──────────────┘      │
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │ MessageBuilder  │
              └─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ MatriceStream   │
              └─────────────────┘
```

## Streaming Loop Flow

```
1. Prepare source (download if URL) → VideoCaptureManager
2. Setup topic → CameraStreamer
3. OUTER LOOP (Retry Forever):
   ├─ Open capture → VideoCaptureManager
   ├─ Get properties → VideoCaptureManager
   ├─ Calculate skip rate → VideoCaptureManager
   └─ INNER LOOP (Process Frames):
      ├─ Read frame → OpenCV
      ├─ Check failures → RetryManager
      ├─ Skip if needed → FrameProcessor
      ├─ Resize frame → FrameProcessor
      ├─ Build metadata → MessageBuilder
      ├─ Encode frame → EncoderManager
      ├─ Build message → MessageBuilder
      ├─ Send message → MatriceStream
      └─ Update stats → StreamStatistics
4. On failure:
   ├─ Log error → RetryManager
   ├─ Exponential backoff → RetryManager
   └─ RETRY (goto step 3)
```

## Configuration Classes

Each module has its own configuration class:

- **VideoSourceConfig** - Capture retry, download timeouts
- **EncoderConfig** - Encoding quality, chunk sizes
- **RetryConfig** - Retry delays, failure thresholds
- **StreamStatistics.STATS_LOG_INTERVAL** - Logging frequency

This makes tuning behavior simple and centralized.

---

## Benefits of New Architecture

### 🎯 **Single Responsibility**
Each class has ONE job and does it well.

### 🧪 **Testable**
Each component can be tested in isolation with mocks.

### 🔧 **Maintainable**
Changes to one component don't affect others.

### 📈 **Scalable**
Easy to add new features (e.g., new encoders, new source types).

### 🛡️ **Robust**
Comprehensive error handling with infinite retry logic.

### 📚 **Readable**
Clear structure, well-documented, easy to understand.

### ♻️ **Reusable**
Components can be used independently or in other projects.

---

## Example Usage

```python
from matrice_streaming.streaming_gateway import CameraStreamer

# Initialize with modular components
streamer = CameraStreamer(
    session=session,
    service_id="my_deployment",
    server_type="kafka",
    h265_mode="frame",
    h265_quality=23
)

# Register topic
streamer.register_stream_topic("camera_1", "video_input_topic")

# Start streaming (will retry forever on failures)
streamer.start_background_stream(
    input="rtsp://camera.example.com/stream",
    fps=30,
    stream_key="camera_1",
    camera_location="Warehouse A"
)

# Get statistics
stats = streamer.get_transmission_stats()
print(f"Frames sent: {stats['frames_sent_full']}")

# Stop when done
streamer.stop_streaming()
await streamer.close()
```

---

## Migration Notes

The refactored `CameraStreamer` maintains **full backward compatibility** with the original API. All public methods have the same signatures, so existing code will work without changes.

### Internal Changes Only
- Helper classes are private implementation details
- Public API remains identical
- Same parameters, same behavior
- Better error handling and retry logic

---

## Future Enhancements

With this modular architecture, future enhancements are straightforward:

1. **New Encoders** - Add to `EncoderManager`
2. **New Source Types** - Extend `VideoCaptureManager`
3. **Advanced Statistics** - Enhance `StreamStatistics`
4. **Custom Retry Policies** - Configure `RetryManager`
5. **Message Formats** - Extend `MessageBuilder`

---

## Summary

The refactored `CameraStreamer` is:
- ✅ **Simpler** - Main class is half the size
- ✅ **More robust** - Never gives up, always retries
- ✅ **Better organized** - Clear separation of concerns
- ✅ **Easier to test** - Modular components
- ✅ **Easier to maintain** - Changes are localized
- ✅ **Easier to extend** - Add features without touching core logic

The code is now **production-ready**, **maintainable**, and follows **best practices** for Python software architecture.

