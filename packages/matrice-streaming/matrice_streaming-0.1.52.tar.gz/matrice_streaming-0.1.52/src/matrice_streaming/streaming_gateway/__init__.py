"""Streaming Gateway package for matrice_streaming."""

from .camera_streamer import CameraStreamer
from .streaming_gateway import StreamingGateway
from .streaming_gateway_utils import StreamingGatewayUtil, InputStream
from .streaming_action import StreamingAction

# Simple camera events
from .event_listener import EventListener
from .dynamic_camera_manager import DynamicCameraManager

# Debug module for testing without external dependencies
from .debug import (
    DebugStreamingGateway,
    DebugStreamingAction,
    DebugStreamBackend,
    MockSession,
    MockRPC
)

__all__ = [
    'CameraStreamer',
    'StreamingGateway', 
    'StreamingGatewayUtil',
    'InputStream',
    'StreamingAction',
    # Camera events
    'EventListener',
    'DynamicCameraManager',
    # Debug exports
    'DebugStreamingGateway',
    'DebugStreamingAction',
    'DebugStreamBackend',
    'MockSession',
    'MockRPC',
]