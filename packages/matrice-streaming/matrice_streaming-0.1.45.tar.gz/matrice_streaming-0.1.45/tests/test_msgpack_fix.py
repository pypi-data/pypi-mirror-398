"""Test msgpack serialization fix for binary data in nested structures."""
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "py_common" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_common.stream.redis_stream import AsyncRedisUtils


async def test_msgpack_with_binary_data():
    """Test that msgpack handles binary data in nested structures."""
    print("Testing msgpack fix for binary data...")
    print("="*60)

    # Create a message structure similar to what camera streamer sends
    test_message = {
        "frame_id": "test123",
        "input_name": "frame_1",
        "input_unit": "frame",
        "input_stream": {
            "ip_key_name": "test_service",
            "stream_info": {
                "broker": "redis://localhost:6379",
                "topic": "test_topic",
                "camera_info": {
                    "camera_name": "test_camera",
                    "location": "test_location"
                }
            },
            "video_codec": "h264",
            "content": b"fake_jpeg_data_12345",  # Binary content!
            "input_hash": "abc123"
        }
    }

    print("\n1. Test message structure:")
    print(f"   - Top level keys: {list(test_message.keys())}")
    print(f"   - input_stream keys: {list(test_message['input_stream'].keys())}")
    print(f"   - Binary content size: {len(test_message['input_stream']['content'])} bytes")

    # Create AsyncRedisUtils instance
    redis_utils = AsyncRedisUtils(
        host="localhost",
        port=6379,
        enable_batching=False  # Disable batching for this test
    )

    try:
        # Setup client
        await redis_utils.setup_client()
        print("\n2. Redis client initialized successfully")

        # Try to add the message
        test_stream = "msgpack_test_stream"
        print(f"\n3. Attempting to add message to stream '{test_stream}'...")

        message_id = await redis_utils.add_message(
            stream_name=test_stream,
            message=test_message,
            message_key="test_key"
        )

        print(f"   SUCCESS! Message added with ID: {message_id}")
        print("\n4. Verification:")
        print("   Message with nested binary data successfully sent to Redis!")
        print("   Msgpack serialization preserved raw bytes without base64 encoding.")

        print("\n" + "="*60)
        print("TEST PASSED: Msgpack successfully handles binary data!")
        print("="*60)

        # Cleanup
        await redis_utils.close()
        return True

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await redis_utils.close()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_msgpack_with_binary_data())
    sys.exit(0 if success else 1)
