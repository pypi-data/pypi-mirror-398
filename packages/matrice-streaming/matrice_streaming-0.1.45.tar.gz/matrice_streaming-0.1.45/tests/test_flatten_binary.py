"""Test flattening approach for binary data in Redis Streams."""
import json


def test_flattening_logic():
    """Test the flatten/reconstruct logic for binary content."""
    print("Testing Redis Stream flattening for binary data...")
    print("="*60)

    # Original message structure (like camera streamer creates)
    original_message = {
        "frame_id": "test_frame_123",
        "input_name": "frame_1",
        "input_unit": "frame",
        "input_stream": {
            "ip_key_name": "test_service",
            "stream_info": {
                "broker": "redis://localhost:6379",
                "topic": "test_topic"
            },
            "video_codec": "h264",
            "content": b"fake_jpeg_data_12345",  # Binary content!
            "input_hash": "abc123"
        }
    }

    print("\n1. Original structure:")
    print(f"   - input_stream has 'content' field: {len(original_message['input_stream']['content'])} bytes")

    # FLATTENING (what streaming gateway does)
    print("\n2. Flattening (streaming gateway):")

    flattened_fields = {}
    for key, value in original_message.items():
        if isinstance(value, dict):
            # Extract binary content
            extracted_content = None
            cleaned_dict = {}

            for nested_k, nested_v in value.items():
                if nested_k == 'content' and isinstance(nested_v, bytes):
                    extracted_content = nested_v
                else:
                    cleaned_dict[nested_k] = nested_v

            # Store as separate fields
            if extracted_content:
                flattened_fields[f"{key}__content"] = extracted_content
                print(f"   - Extracted: {key}__content ({len(extracted_content)} bytes)")

            # JSON serialize the rest
            flattened_fields[key] = json.dumps(cleaned_dict)
            print(f"   - JSON serialized: {key}")
        else:
            flattened_fields[key] = value

    print(f"\n   Total fields in Redis: {len(flattened_fields)}")
    print(f"   Fields: {list(flattened_fields.keys())}")

    # RECONSTRUCTION (what inference pipeline does)
    print("\n3. Reconstruction (inference pipeline):")

    result = {}
    binary_fields = {}

    # First pass: identify binary fields
    for key, value in flattened_fields.items():
        if '__content' in key:
            base_key = key.replace('__content', '')
            binary_fields[base_key] = value
        else:
            result[key] = value

    # Second pass: merge binary back
    for base_key, binary_content in binary_fields.items():
        if base_key in result:
            if isinstance(result[base_key], str):
                # Parse JSON and add content
                nested_dict = json.loads(result[base_key])
                if isinstance(nested_dict, dict):
                    nested_dict['content'] = binary_content
                    result[base_key] = nested_dict
                    print(f"   - Reconstructed: {base_key} with content ({len(binary_content)} bytes)")

    print("\n4. Verification:")
    print(f"   - Reconstructed keys: {list(result.keys())}")

    if isinstance(result.get("input_stream"), dict):
        input_stream = result["input_stream"]
        print(f"   - input_stream is dict: YES")
        print(f"   - input_stream has 'content': {'YES' if 'content' in input_stream else 'NO'}")

        if 'content' in input_stream:
            content = input_stream['content']
            if isinstance(content, bytes):
                print(f"   - content is bytes: YES ({len(content)} bytes)")
                if content == original_message['input_stream']['content']:
                    print("   - content matches original: YES")
                    print("\n" + "="*60)
                    print("TEST PASSED!")
                    print("="*60)
                    print("\nBenefits:")
                    print("  - No msgpack dependency")
                    print("  - No base64 encoding (33% overhead saved)")
                    print("  - Uses Redis binary-safe fields directly")
                    print("  - Simple JSON for metadata")
                    print("  - Raw bytes for binary content")
                    return True
                else:
                    print("   - ERROR: content doesn't match!")
                    return False
            else:
                print(f"   - ERROR: content is not bytes: {type(content)}")
                return False
        else:
            print("   - ERROR: 'content' field missing!")
            return False
    else:
        print("   - ERROR: input_stream is not a dict!")
        return False


if __name__ == "__main__":
    try:
        success = test_flattening_logic()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
