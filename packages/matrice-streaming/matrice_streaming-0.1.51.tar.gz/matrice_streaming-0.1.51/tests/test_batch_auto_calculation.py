"""Test automatic batch parameter calculation based on camera count."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_streaming.streaming_gateway.camera_streamer.camera_streamer import CameraStreamer


def test_batch_parameter_calculation():
    """Test that batch parameters scale correctly with camera count."""

    test_cases = [
        # (num_cameras, expected_batch_size, expected_timeout_ms)
        (1, 10, 10),           # Single camera: conservative
        (5, 10, 10),           # Few cameras: conservative
        (10, 10, 10),          # 10 cameras: still conservative
        (20, 50, 20),          # Small deployment
        (50, 50, 20),          # Small deployment max
        (100, 100, 50),        # Medium deployment
        (200, 100, 50),        # Medium deployment max
        (300, 250, 100),       # Large deployment
        (500, 250, 100),       # Large deployment max
        (1000, 500, 100),      # Very large: maximum throughput
    ]

    print("Testing automatic batch parameter calculation:\n")
    print(f"{'Cameras':<10} {'Batch Size':<12} {'Timeout (ms)':<15} {'Status':<10}")
    print("-" * 50)

    all_passed = True
    for num_cameras, expected_batch_size, expected_timeout_ms in test_cases:
        params = CameraStreamer.calculate_batch_parameters(num_cameras)

        batch_size = params['batch_size']
        timeout_ms = params['batch_timeout'] * 1000

        # Verify expectations
        size_match = batch_size == expected_batch_size
        timeout_match = abs(timeout_ms - expected_timeout_ms) < 0.1

        status = "[PASS]" if (size_match and timeout_match) else "[FAIL]"
        if not (size_match and timeout_match):
            all_passed = False

        print(f"{num_cameras:<10} {batch_size:<12} {timeout_ms:<15.1f} {status:<10}")

    print("\n" + "=" * 50)
    if all_passed:
        print("All tests PASSED!")
        print("\nBatch parameter scaling verified:")
        print("  - 1-10 cameras: Low latency (10ms, batch=10)")
        print("  - 11-50 cameras: Balanced (20ms, batch=50)")
        print("  - 51-200 cameras: Medium throughput (50ms, batch=100)")
        print("  - 201-500 cameras: High throughput (100ms, batch=250)")
        print("  - 500+ cameras: Maximum throughput (100ms, batch=500)")
        return True
    else:
        print("Some tests FAILED!")
        return False


if __name__ == "__main__":
    success = test_batch_parameter_calculation()
    sys.exit(0 if success else 1)
