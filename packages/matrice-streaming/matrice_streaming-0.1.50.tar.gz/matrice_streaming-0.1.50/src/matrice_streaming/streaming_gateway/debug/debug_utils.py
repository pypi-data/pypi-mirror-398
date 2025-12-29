"""Debug utilities and mock data generators."""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MockRPC:
    """Mock RPC client for testing without real API."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("[DEBUG] MockRPC initialized")
    
    def get(self, path: str) -> Dict[str, Any]:
        """Mock GET request."""
        self.logger.info(f"[DEBUG API] GET {path}")
        
        # Mock responses for different endpoints
        if "streaming_gateways" in path:
            return self._mock_streaming_gateway_response()
        elif "all_camera_groups_by_gateway_id" in path:
            return self._mock_camera_groups_response()
        elif "all_camera_by_streaming_gateway_id" in path:
            return self._mock_cameras_response()
        elif "get_simulated_stream_url" in path:
            return self._mock_simulated_stream_url_response()
        elif "get_topics_by_streaming_id_and_server_id" in path:
            return self._mock_topics_response(path)
        elif "get_kafka_server" in path:
            return self._mock_kafka_server_response()
        elif "redis_servers" in path:
            return self._mock_redis_server_response()
        elif "action" in path and "details" in path:
            return self._mock_action_details_response()
        else:
            return {"success": True, "data": {}}
    
    def post(self, path: str, payload: Dict = None) -> Dict[str, Any]:
        """Mock POST request."""
        self.logger.info(f"[DEBUG API] POST {path}")
        return {"success": True, "data": {"message": "Operation successful"}}
    
    def put(self, path: str, payload: Dict = None) -> Dict[str, Any]:
        """Mock PUT request."""
        self.logger.info(f"[DEBUG API] PUT {path}")
        return {"success": True, "data": {"message": "Update successful"}}
    
    def _mock_streaming_gateway_response(self) -> Dict[str, Any]:
        """Mock streaming gateway details."""
        return {
            "success": True,
            "data": {
                "id": "debug_gateway_001",
                "accountNumber": "debug_account",
                "accountType": "enterprise",
                "gatewayName": "Debug Streaming Gateway",
                "description": "Debug mode gateway for testing",
                "status": "running",
                "actionRecordID": "debug_action_001",
                "serverId": "debug_server_001",
                "serverType": "debug",
                "networkSettings": {
                    "IPAddress": "127.0.0.1",
                    "port": 9092,
                    "accessScale": "local",
                    "region": "DEBUG"
                },
                "userID": "debug_user_001",
            }
        }
    
    def _mock_camera_groups_response(self) -> Dict[str, Any]:
        """Mock camera groups."""
        return {
            "success": True,
            "data": [
                {
                    "id": "debug_group_001",
                    "accountNumber": "debug_account",
                    "cameraGroupName": "Debug Camera Group 1",
                    "locationId": "debug_location_001",
                    "streamingGatewayId": "debug_gateway_001",
                    "defaultStreamSettings": {
                        "make": "Debug",
                        "model": "Debug Cam",
                        "aspectRatio": "16:9",
                        "height": 480,
                        "width": 640,
                        "videoQuality": 80,
                        "streamingFPS": 10
                    }
                }
            ]
        }
    
    def _mock_cameras_response(self) -> Dict[str, Any]:
        """Mock cameras list."""
        return {
            "success": True,
            "data": [
                {
                    "id": "debug_camera_001",
                    "accountNumber": "debug_account",
                    "cameraName": "Debug Camera 1",
                    "cameraGroupId": "debug_group_001",
                    "streamingGatewayId": "debug_gateway_001",
                    "cameraFeedPath": "",
                    "simulationVideoPath": "",  # Will be overridden
                    "protocolType": "FILE",
                    "customStreamSettings": {}
                }
            ]
        }
    
    def _mock_simulated_stream_url_response(self) -> Dict[str, Any]:
        """Mock simulated stream URL."""
        return {
            "success": True,
            "data": {
                "streamType": "FILE",
                "url": ""  # Will be set by user
            }
        }
    
    def _mock_topics_response(self, path: str) -> Dict[str, Any]:
        """Mock topics."""
        if "topicType=input" in path:
            return {
                "success": True,
                "data": [
                    {
                        "id": "debug_topic_001",
                        "accountNumber": "debug_account",
                        "cameraId": "debug_camera_001",
                        "streamingGatewayId": "debug_gateway_001",
                        "topicName": "debug_input_topic",
                        "topicType": "input"
                    }
                ]
            }
        else:
            return {
                "success": True,
                "data": [
                    {
                        "id": "debug_topic_002",
                        "accountNumber": "debug_account",
                        "cameraId": "debug_camera_001",
                        "streamingGatewayId": "debug_gateway_001",
                        "topicName": "debug_output_topic",
                        "topicType": "output"
                    }
                ]
            }
    
    def _mock_kafka_server_response(self) -> Dict[str, Any]:
        """Mock Kafka server info."""
        return {
            "success": True,
            "data": {
                "ipAddress": "127.0.0.1",
                "port": "9092",
                "status": "running"
            }
        }
    
    def _mock_redis_server_response(self) -> Dict[str, Any]:
        """Mock Redis server info."""
        return {
            "success": True,
            "data": {
                "host": "127.0.0.1",
                "port": 6379,
                "status": "running",
                "password": "",
                "username": "",
                "db": 0
            }
        }
    
    def _mock_action_details_response(self) -> Dict[str, Any]:
        """Mock action details."""
        return {
            "success": True,
            "data": {
                "action": "start_streaming",
                "_idProject": "debug_project_001",
                "_idService": "debug_gateway_001",
                "serviceName": "Debug Streaming",
                "actionDetails": {
                    "serverId": "debug_server_001",
                    "serverType": "debug",
                    "video_codec": "h265-frame"
                },
                "jobParams": {
                    "video_codec": "h265-frame"
                },
                "account_number": "debug_account"
            }
        }


@dataclass
class MockSession:
    """Mock session for testing without authentication."""
    
    def __init__(self):
        self.rpc = MockRPC()
        self.logger = logging.getLogger(__name__)
        self.logger.info("[DEBUG] MockSession initialized")


def create_debug_video_config(video_paths: List[str]) -> List[Dict[str, Any]]:
    """Create debug configuration from video file paths.
    
    Args:
        video_paths: List of video file paths to stream
        
    Returns:
        List of camera configurations
    """
    configs = []
    
    for i, video_path in enumerate(video_paths):
        config = {
            "id": f"debug_camera_{i:03d}",
            "accountNumber": "debug_account",
            "cameraName": f"Debug Camera {i+1}",
            "cameraGroupId": "debug_group_001",
            "streamingGatewayId": "debug_gateway_001",
            "cameraFeedPath": "",
            "simulationVideoPath": video_path,
            "protocolType": "FILE",
            "customStreamSettings": {
                "streamingFPS": 10,
                "videoQuality": 80,
                "width": 640,
                "height": 480
            }
        }
        configs.append(config)
    
    return configs


def create_debug_input_streams(video_paths: List[str], fps: int = 10, loop: bool = True) -> List:
    """Create InputStream objects for debug mode.
    
    Args:
        video_paths: List of video file paths
        fps: Frames per second
        loop: Whether to loop video files
        
    Returns:
        List of InputStream objects
    """
    from ..streaming_gateway_utils import InputStream
    
    input_streams = []
    
    for i, video_path in enumerate(video_paths):
        stream = InputStream(
            source=video_path,
            fps=fps,
            quality=80,
            width=640,
            height=480,
            camera_id=f"debug_camera_{i:03d}",
            camera_key=f"Debug_Camera_{i+1}",
            camera_group_key="Debug_Camera_Group",
            camera_location="Debug_Location",
            camera_input_topic=f"debug_input_topic_{i}",
            camera_connection_info={},
            simulate_video_file_stream=loop
        )
        input_streams.append(stream)
    
    return input_streams


def create_camera_configs_from_streams(input_streams: List) -> List[Dict[str, Any]]:
    """Convert InputStream objects to camera configs for WorkerManager.

    Args:
        input_streams: List of InputStream objects

    Returns:
        List of camera configuration dictionaries for WorkerManager
    """
    camera_configs = []

    for stream in input_streams:
        config = {
            'source': stream.source,
            'stream_key': stream.camera_key,
            'stream_group_key': stream.camera_group_key,
            'topic': stream.camera_input_topic,
            'fps': stream.fps,
            'quality': stream.quality,
            'width': stream.width,
            'height': stream.height,
            'simulate_video_file_stream': stream.simulate_video_file_stream,
            'camera_location': stream.camera_location,
        }
        camera_configs.append(config)

    return camera_configs

