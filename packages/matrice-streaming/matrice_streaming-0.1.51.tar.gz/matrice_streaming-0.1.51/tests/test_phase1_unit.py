"""Unit tests for Phase 1 components (without full multiprocessing)."""
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from matrice_streaming.streaming_gateway.camera_streamer.encoding_pool_manager import EncodingPoolManager


class TestEncodingPoolManager:
    """Test encoding pool manager."""

    def test_init_default_workers(self):
        """Test initialization with default worker count."""
        manager = EncodingPoolManager()
        import multiprocessing
        expected_workers = max(2, multiprocessing.cpu_count() - 2)
        assert manager.num_workers == expected_workers

    def test_init_custom_workers(self):
        """Test initialization with custom worker count."""
        manager = EncodingPoolManager(num_workers=4)
        assert manager.num_workers == 4

    def test_start_stop(self):
        """Test starting and stopping pool."""
        manager = EncodingPoolManager(num_workers=2)
        assert not manager.is_running()

        manager.start()
        assert manager.is_running()
        assert manager.pool is not None

        manager.stop()
        assert not manager.is_running()
        assert manager.pool is None

    def test_context_manager(self):
        """Test context manager usage."""
        with EncodingPoolManager(num_workers=2) as manager:
            assert manager.is_running()
            pool = manager.get_pool()
            assert pool is not None

        assert not manager.is_running()

    def test_get_pool_not_started(self):
        """Test getting pool when not started raises error."""
        manager = EncodingPoolManager(num_workers=2)

        with pytest.raises(RuntimeError, match="not started"):
            manager.get_pool()


class TestAsyncCameraWorkerComponents:
    """Test async camera worker components."""

    @pytest.mark.asyncio
    async def test_encode_frame_async_mock(self):
        """Test async frame encoding with mocked pool."""
        from matrice_streaming.streaming_gateway.camera_streamer.async_camera_worker import AsyncCameraWorker
        import numpy as np
        import multiprocessing

        # Create mock components
        mock_stop_event = Mock()
        mock_stop_event.is_set.return_value = False
        mock_health_queue = Mock()

        camera_configs = [{
            'stream_key': 'test_camera',
            'stream_group_key': 'test_group',
            'source': 0,
            'topic': 'test_topic',
            'fps': 10,
            'quality': 80
        }]

        stream_config = {
            'service_id': 'test',
            'host': 'localhost',
            'port': 6379
        }

        # Create worker (don't run it)
        worker = AsyncCameraWorker(
            worker_id=0,
            camera_configs=camera_configs,
            stream_config=stream_config,
            stop_event=mock_stop_event,
            health_queue=mock_health_queue
        )

        # Create mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Mock the executor result
        mock_future = asyncio.Future()
        mock_future.set_result((True, np.array([1, 2, 3, 4, 5], dtype=np.uint8)))

        # Test encoding with mocked executor
        loop = asyncio.get_running_loop()
        with patch.object(loop, 'run_in_executor', return_value=mock_future):
            frame_data, codec = await worker._encode_frame_async(frame, 90)

            assert frame_data == b'\x01\x02\x03\x04\x05'
            assert codec == "h264"

    @pytest.mark.asyncio
    async def test_health_reporting(self):
        """Test health reporting mechanism."""
        from matrice_streaming.streaming_gateway.camera_streamer.async_camera_worker import AsyncCameraWorker
        import multiprocessing
        import queue

        mock_stop_event = Mock()
        mock_stop_event.is_set.return_value = False
        mock_health_queue = multiprocessing.Manager().Queue()

        camera_configs = []
        stream_config = {'service_id': 'test', 'host': 'localhost', 'port': 6379}

        worker = AsyncCameraWorker(
            worker_id=42,
            camera_configs=camera_configs,
            stream_config=stream_config,
            stop_event=mock_stop_event,
            health_queue=mock_health_queue
        )

        # Report health
        worker._report_health("running", active_cameras=5)

        # Check report
        try:
            report = mock_health_queue.get(timeout=1.0)
            assert report['worker_id'] == 42
            assert report['status'] == "running"
            assert report['active_cameras'] == 5
            assert 'timestamp' in report
        except queue.Empty:
            pytest.fail("Health report not received")


class TestZeroCopyOptimization:
    """Test zero-copy optimizations."""

    def test_bytes_from_numpy_buffer(self):
        """Test zero-copy bytes conversion from numpy array."""
        import numpy as np

        # Create numpy array (simulates JPEG buffer from cv2.imencode)
        jpeg_buffer = np.array([0xFF, 0xD8, 0xFF, 0xE0], dtype=np.uint8)

        # Zero-copy conversion
        frame_data = bytes(jpeg_buffer.data)

        assert frame_data == b'\xff\xd8\xff\xe0'
        assert isinstance(frame_data, bytes)

    def test_memoryview_cast(self):
        """Test memoryview cast for zero-copy."""
        import numpy as np

        # Create frame
        frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Zero-copy with memoryview
        frame_data = bytes(memoryview(frame).cast('B'))

        assert len(frame_data) == 100 * 100 * 3
        assert isinstance(frame_data, bytes)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
