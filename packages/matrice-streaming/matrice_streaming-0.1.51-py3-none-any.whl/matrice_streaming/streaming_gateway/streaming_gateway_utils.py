from dataclasses import dataclass
import re
from typing import Optional, Union, Dict, List
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from matrice_common.session import Session


@dataclass
class InputStream:
    """Configuration for input sources."""

    source: Union[int, str]  # Camera index, file path, or stream URL
    fps: int = 10
    quality: int = 100
    width: Optional[int] = 640
    height: Optional[int] = 480
    camera_id: Optional[str] = None
    camera_key: Optional[str] = "Unknown Camera"
    camera_group_key: Optional[str] = "Unknown Camera Group"
    camera_location: Optional[str] = "Unknown Camera Location"
    camera_input_topic: str = None
    camera_connection_info: dict = None
    simulate_video_file_stream: bool = False


class StreamingGatewayUtil:

    def __init__(
        self, session: Session, streaming_gateway_id: str, server_id: str = None, action_id: str = None
    ):
        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.server_id = server_id
        self.action_id = action_id
        if not self.server_id and self.streaming_gateway_id:
            self.server_id = self.get_streaming_gateway_by_id().get("serverId")
        
        # Initialize heartbeat reporter for Kafka
        self._heartbeat_reporter = None
        self._init_heartbeat_reporter()
    
    def _init_heartbeat_reporter(self):
        """Initialize the Kafka heartbeat reporter."""
        try:
            from .metrics_reporter import HeartbeatReporter
            self._heartbeat_reporter = HeartbeatReporter(
                self.session,
                self.streaming_gateway_id,
                topic="streaming_gateway_heartbeat"
            )
            logging.info("Heartbeat reporter initialized for streaming gateway")
        except Exception as e:
            logging.warning(f"Failed to initialize heartbeat reporter: {e}")

    def _parse_response(self, resp: dict):
        if resp.get("success"):
            return resp.get("data")
        else:
            logging.error("Request failed with payload: %s", resp, exc_info=True)
        return None

    def get_streaming_gateway_by_id(self):
        if not self.streaming_gateway_id:
            raise ValueError("Streaming gateway ID is required")
        return self._parse_response(
            self.session.rpc.get(
                f"/v1/inference/get_streaming_gateways/{self.streaming_gateway_id}"
            )
        )

    #     {'id': '68c43cee7b628ecd0d44c0ca',
    #   'accountNumber': '2276842692221978464767135',
    #   'accountType': 'enterprise',
    #   'gatewayName': 'Test_App_Deployment',
    #   'description': 'Testing',
    #   'status': 'created',
    #   'actionRecordID': '000000000000000000000000',
    #   'startTime': '0001-01-01T00:00:00Z',
    #   'lastStreamTime': '0001-01-01T00:00:00Z',
    #   'serverId': '68c43ceed0e26ec0da43eb3a',
    #   'serverType': 'redis',
    #   'networkSettings': {'IPAddress': '0.0.0.0',
    #    'port': 80,
    #    'accessScale': 'regional',
    #    'region': 'US'},
    #   'userID': '6819bdda7481e811e530a84a',
    #   'createdAt': '2025-09-12T15:31:58.359Z',
    #   'updatedAt': '2025-09-12T15:31:59.298Z'}

    def get_camera_groups(self):
        return self._parse_response(
            self.session.rpc.get(
                f"/v1/inference/all_camera_groups_by_gateway_id/{self.streaming_gateway_id}"
            )
        )

    #         [{'id': '68bfdc599c892544110d024b',
    #   'accountNumber': '2276842692221978464767135',
    #   'cameraGroupName': 'Testing Cam 21',
    #   'locationId': '68be42397d9f7cbe2efa4fee',
    #   'streamingGatewayId': '68be77a634feaa4ecc8ee942',
    #   'defaultStreamSettings': {'make': 'Model',
    #    'model': 'Modle 2',
    #    'aspectRatio': '16:9',
    #    'height': 1080,
    #    'width': 1920,
    #    'videoQuality': 80,
    #    'streamingFPS': 30},
    #   'createdAt': '2025-09-09T07:50:49.339Z',
    #   'updatedAt': '2025-09-09T07:50:49.339Z'}]

    def get_cameras(self):
        return self._parse_response(
            self.session.rpc.get(
                f"/v1/inference/all_camera_by_streaming_gateway_id/{self.streaming_gateway_id}"
            )
        )

    #     [{'id': '68bfdd509c892544110d024d',
    #   'accountNumber': '2276842692221978464767135',
    #   'cameraName': 'Cam_Test',
    #   'cameraGroupId': '68bfdc599c892544110d024b',
    #   'streamingGatewayId': '68be77a634feaa4ecc8ee942',
    #   'cameraFeedPath': '',
    #   'simulationVideoPath': 'https://s3.us-west-2.amazonaws.com/dev.application.predictions/2adb24f1495e9afe086fcamera-video-1757404340861.mp4',
    #   'protocolType': 'FILE',
    #   'customStreamSettings': {},
    #   'createdAt': '2025-09-09T07:54:56.189Z',
    #   'updatedAt': '2025-09-09T07:54:56.189Z'}]

    def get_simulated_stream_url(self, camera_id: str):
        return self._parse_response(
            self.session.rpc.get(f"/v1/inference/get_simulated_stream_url/{camera_id}")
        )

    #     {'streamType': 'FILE',
    # 'url': 'https://s3.us-west-2.amazonaws.com/dev.application.predictions/2adb24f1495e9afe086fcamera-video-1757404340861.mp4?X-Amz-Algorithm=AWS4-HMA'}

    def get_streaming_input_topics(self):
        return self._parse_response(
            self.session.rpc.get(
                f"/v1/inference/get_topics_by_streaming_id_and_server_id/{self.streaming_gateway_id}/{self.server_id}?topicType=input"
            )
        )

    #         [{'id': '68bfdd509c892544110d024e',
    #   'accountNumber': '2276842692221978464767135',
    #   'cameraId': '68bfdd509c892544110d024d',
    #   'streamingGatewayId': '68be77a634feaa4ecc8ee942',
    #   'topicName': '68bfdd509c892544110d024d_input_topic',
    #   'topicType': 'input'}]

    def get_streaming_output_topics(self):
        return self._parse_response(
            self.session.rpc.get(
                f"/v1/inference/get_topics_by_streaming_id_and_server_id/{self.streaming_gateway_id}/{self.server_id}?topicType=output"
            )
        )

    def get_input_streams(self) -> List[InputStream]:
        """Get cameras as list of InputStream objects with proper configuration."""
        # Time the first 3 API calls
        start = time.time()
        cameras = self.get_cameras()
        cameras_time = time.time() - start
        logging.info(f"API call get_cameras() took {cameras_time:.3f}s")

        start = time.time()
        camera_groups = self.get_camera_groups()
        groups_time = time.time() - start
        logging.info(f"API call get_camera_groups() took {groups_time:.3f}s")

        start = time.time()
        input_topics = self.get_streaming_input_topics()
        topics_time = time.time() - start
        logging.info(f"API call get_streaming_input_topics() took {topics_time:.3f}s")

        if not cameras:
            logging.warning("No cameras found for streaming gateway")
            return []

        # Create lookup dictionaries
        camera_group_lookup = {group["id"]: group for group in (camera_groups or [])}
        topic_lookup = {
            topic["cameraId"]: topic["topicName"] for topic in (input_topics or [])
        }

        # Identify FILE cameras that need simulated stream URLs
        file_cameras = [c for c in cameras if c.get("protocolType") == "FILE"]

        # Fetch simulated URLs concurrently, with caching for cameras sharing the same simulationVideoPath
        stream_url_lookup = {}
        if file_cameras:
            # Group cameras by simulationVideoPath to avoid redundant API calls
            # Only group non-empty paths; empty paths need individual API calls
            path_to_cameras: Dict[str, List[dict]] = {}
            cameras_needing_api_call = []
            
            for camera in file_cameras:
                sim_path = camera.get("simulationVideoPath", "")
                if sim_path:  # Non-empty path - can potentially share URL
                    if sim_path not in path_to_cameras:
                        path_to_cameras[sim_path] = []
                        # First camera with this path will make the API call
                        cameras_needing_api_call.append(camera)
                    path_to_cameras[sim_path].append(camera)
                else:
                    # Empty path - needs its own API call
                    cameras_needing_api_call.append(camera)
            
            logging.info(
                f"FILE cameras: {len(file_cameras)} total, {len(cameras_needing_api_call)} unique API calls needed "
                f"({len(file_cameras) - len(cameras_needing_api_call)} will use cached URLs)"
            )
            
            max_workers = min(len(cameras_needing_api_call), 100)  # Max 100 concurrent requests
            start = time.time()
            
            # Cache to store presigned URL by simulationVideoPath
            path_url_cache: Dict[str, str] = {}
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_camera = {
                    executor.submit(self.get_simulated_stream_url, c["id"]): c
                    for c in cameras_needing_api_call
                }
                for future in as_completed(future_to_camera):
                    camera = future_to_camera[future]
                    camera_id = camera["id"]
                    sim_path = camera.get("simulationVideoPath", "")
                    try:
                        result = future.result()
                        if result and result.get("url"):
                            presigned_url = result["url"]
                            stream_url_lookup[camera_id] = presigned_url
                            # Cache the URL for this simulationVideoPath
                            if sim_path:
                                path_url_cache[sim_path] = presigned_url
                    except Exception as e:
                        logging.warning(f"Failed to get stream URL for camera {camera_id}: {e}")
            
            # Apply cached URLs to cameras that share the same simulationVideoPath
            for sim_path, cameras_with_path in path_to_cameras.items():
                if sim_path in path_url_cache:
                    cached_url = path_url_cache[sim_path]
                    for camera in cameras_with_path:
                        # Only set if not already set (the first camera already has it)
                        if camera["id"] not in stream_url_lookup:
                            stream_url_lookup[camera["id"]] = cached_url

            urls_time = time.time() - start
            logging.info(
                f"Concurrent fetch of {len(cameras_needing_api_call)} stream URLs took {urls_time:.3f}s "
                f"(max_workers={max_workers}, cached {len(file_cameras) - len(cameras_needing_api_call)} URLs)"
            )

        input_streams = []

        for camera in cameras:
            camera_id = camera["id"]
            camera_group_id = camera.get("cameraGroupId")
            camera_group = camera_group_lookup.get(camera_group_id, {})

            # Get default settings from camera group
            default_settings = camera_group.get("defaultStreamSettings", {})
            custom_settings = camera.get("customStreamSettings", {})

            # Merge settings (custom overrides default)
            settings = {**default_settings, **custom_settings}

            # Determine source URL
            source = camera.get("cameraFeedPath", "")
            simulate_video = False

            if camera.get("protocolType") == "FILE":
                # Use pre-fetched URL from concurrent lookup
                if camera_id in stream_url_lookup:
                    source = stream_url_lookup[camera_id]
                    simulate_video = True
                else:
                    # Fallback to simulation video path
                    source = camera.get("simulationVideoPath", "")
                    simulate_video = True

            # Get input topic for this camera
            input_topic = topic_lookup.get(camera_id)

            # Create InputStream object
            input_stream = InputStream(
                source=source,
                fps=settings.get("streamingFPS", 10),
                quality=settings.get("videoQuality", 100),
                width=settings.get("width", 640),
                height=settings.get("height", 480),
                camera_id=camera_id,
                camera_key=camera.get("cameraName", "Unknown Camera"),
                camera_group_key=camera_group.get(
                    "cameraGroupName", "Unknown Camera Group"
                ),
                camera_location=camera_group.get(
                    "locationId", "Unknown Camera Location"
                ),
                camera_input_topic=input_topic,
                camera_connection_info=camera,
                simulate_video_file_stream=simulate_video,
            )

            input_streams.append(input_stream)

        logging.info(f"Created {len(input_streams)} input streams for streaming gateway")
        return input_streams

    def start_streaming(self) -> Optional[Dict]:
        """
        Start the streaming gateway.

        Returns:
            Dict: API response data or None if failed
        """
        path = f"/v1/inference/start_streaming_gateway/{self.streaming_gateway_id}"

        resp = self.session.rpc.post(path=path, payload={})

        return self._parse_response(resp)

    def stop_streaming(self) -> Optional[Dict]:
        """
        Stop the streaming gateway.

        Returns:
            Dict: API response data or None if failed
        """
        path = f"/v1/inference/stop_streaming_gateway/{self.streaming_gateway_id}"

        resp = self.session.rpc.post(path=path, payload={})

        return self._parse_response(resp)

    def update_status(self, status: str) -> Optional[Dict]:
        """
        Update the status of the streaming gateway.

        Args:
            status: New status (active, inactive, starting, stopped, etc.)

        Returns:
            Dict: API response data or None if failed
        """
        if not status:
            logging.error("Status is required", exc_info=True)
            return None

        # Use PUT endpoint with status in query params
        path = (
            f"/v1/inference/update_streaming_gateway_status/{self.streaming_gateway_id}?status={status}"
        )

        resp = self.session.rpc.put(path=path, payload={})

        logging.info(f"Updated streaming gateway status to: {status}")
        return self._parse_response(resp)

    def get_and_wait_for_connection_info(
        self, server_type: str = None, server_id: str = None, connection_timeout: int = 300
    ) -> Dict:
        """Get and wait for connection information for the streaming gateway.
        
        Args:
            server_type: Type of server ('kafka' or 'redis'). Required.
            server_id: ID of the server. If not provided, uses self.server_id.
            connection_timeout: Timeout in seconds to wait for connection info (default: 300).
            
        Returns:
            Dict: Connection configuration
            
        Raises:
            ValueError: If server_type or server_id is not provided
            RuntimeError: If timeout is reached while waiting for connection info
        """
        # Use provided server_id or fall back to instance server_id
        server_id = server_id or self.server_id
        
        if not server_id:
            raise ValueError("Server ID is required (provide server_id parameter or set self.server_id)")
        if not server_type:
            raise ValueError("Server type is required")

        def _get_kafka_connection_info():
            try:
                response = self.session.rpc.get(
                    f"/v1/actions/get_kafka_server/{server_id}"
                )
                if response.get("success", False):
                    data = response.get("data")
                    if (
                        data
                        and data.get("ipAddress")
                        and data.get("port")
                        and data.get("status") == "running"
                    ):
                        return {
                            "bootstrap_servers": f'{data["ipAddress"]}:{data["port"]}',
                            "sasl_mechanism": "SCRAM-SHA-256",
                            "sasl_username": "matrice-sdk-user",
                            "sasl_password": "matrice-sdk-password",
                            "security_protocol": "SASL_PLAINTEXT",
                        }
                    else:
                        logging.debug(
                            "Kafka connection information is not complete, waiting..."
                        )
                        return None
                else:
                    logging.debug(
                        "Failed to get Kafka connection information: %s",
                        response.get("message", "Unknown error"),
                    )
                    return None
            except Exception as exc:
                logging.debug("Exception getting Kafka connection info: %s", str(exc))
                return None

        def _get_redis_connection_info():
            try:
                # Build URL with actionId query parameter if available
                url = f"/v1/actions/redis_servers/{server_id}"
                if self.action_id:
                    url += f"?actionId={self.action_id}"
                response = self.session.rpc.get(url)
                if response.get("success", False):
                    data = response.get("data")
                    if (
                        data
                        # TODO: Check why BE is giving host as empty while in the DB it is localhost
                        and data.get("port")
                        and data.get("status") == "running"
                    ):
                        return {
                            "host": data.get("host") or "localhost",
                            "port": int(data["port"]),
                            "password": data.get("password", ""),
                            "username": data.get("username"),
                            "db": data.get("db", 0),
                            "connection_timeout": 30,
                        }
                    else:
                        logging.debug(
                            "Redis connection information is not complete, waiting..."
                        )
                        return None
                else:
                    logging.debug(
                        "Failed to get Redis connection information: %s",
                        response.get("message", "Unknown error"),
                    )
                    return None
            except Exception as exc:
                logging.debug("Exception getting Redis connection info: %s", str(exc))
                return None

        start_time = time.time()
        last_log_time = 0

        while True:
            current_time = time.time()

            # Get connection info based on server type
            connection_info = None
            if server_type == "kafka":
                connection_info = _get_kafka_connection_info()
            elif server_type == "redis":
                connection_info = _get_redis_connection_info()
            else:
                raise ValueError(f"Unsupported server type: {server_type}")

            # If we got valid connection info, return it
            if connection_info:
                logging.info(
                    "Successfully retrieved %s connection information", server_type
                )
                return connection_info

            # Check timeout
            if current_time - start_time > connection_timeout:
                error_msg = f"Timeout waiting for {server_type} connection information after {connection_timeout} seconds"
                logging.error(error_msg)

                # Log the last response for debugging
                try:
                    if server_type == "kafka":
                        response = self.session.rpc.get(
                            f"/v1/actions/get_kafka_server/{server_id}"
                        )
                    else:
                        url = f"/v1/actions/redis_servers/{server_id}"
                        if self.action_id:
                            url += f"?actionId={self.action_id}"
                        response = self.session.rpc.get(url)
                    logging.error("Last response received: %s", response)
                except Exception as exc:
                    logging.error(
                        "Failed to get last response for debugging: %s", str(exc)
                    )

                raise RuntimeError(error_msg)

            # Log waiting message every 10 seconds to avoid spam
            if current_time - last_log_time >= 10:
                elapsed = current_time - start_time
                remaining = connection_timeout - elapsed
                logging.info(
                    "Waiting for %s connection information... (%.1fs elapsed, %.1fs remaining)",
                    server_type,
                    elapsed,
                    remaining,
                )
                last_log_time = current_time

            time.sleep(1)

    def send_heartbeat(self, camera_config: Optional[Dict] = None) -> bool:
        """
        Send a heartbeat to the streaming gateway via Kafka.

        Args:
            camera_config: Camera configuration data to include in heartbeat
                           Should contain 'cameras' list and 'stats' dict

        Returns:
            bool: True if heartbeat sent successfully, False otherwise
        """
        if not self.streaming_gateway_id:
            raise ValueError("Streaming gateway ID is required")

        if not self._heartbeat_reporter:
            logging.warning("Heartbeat reporter not initialized, cannot send heartbeat")
            return False

        # Use provided camera_config or empty structure
        config = camera_config or {"cameras": [], "stats": {}}

        # Send via Kafka
        try:
            success = self._heartbeat_reporter.send_heartbeat(config)
            return success
        except Exception as e:
            logging.error(f"Failed to send heartbeat: {e}", exc_info=True)
            return False


def input_stream_to_camera_config(input_stream: InputStream) -> Dict:
    """Convert InputStream dataclass to camera_config dict for WorkerManager.

    This adapter function converts the InputStream configuration format used by
    StreamingGateway to the dictionary format expected by WorkerManager and
    AsyncCameraWorker.

    Args:
        input_stream: InputStream dataclass instance

    Returns:
        Dict compatible with WorkerManager/AsyncCameraWorker
    """
    return {
        'stream_key': input_stream.camera_key or f"camera_{input_stream.camera_id}",
        'camera_id': input_stream.camera_id,
        'source': input_stream.source,
        'topic': input_stream.camera_input_topic or f"{input_stream.camera_id}_input_topic",
        'fps': input_stream.fps,
        'quality': input_stream.quality,
        'width': input_stream.width,
        'height': input_stream.height,
        'camera_location': input_stream.camera_location or "Unknown",
        'stream_group_key': input_stream.camera_group_key or "default",
        'simulate_video_file_stream': input_stream.simulate_video_file_stream,
    }


def build_stream_config(
    gateway_util: StreamingGatewayUtil,
    server_type: str,
    service_id: str
) -> Dict:
    """Build stream_config dict for WorkerManager from gateway connection info.

    This function retrieves connection information from the API and builds
    a configuration dictionary suitable for WorkerManager and AsyncCameraWorker.

    Args:
        gateway_util: StreamingGatewayUtil instance for API calls
        server_type: 'kafka' or 'redis'
        service_id: Streaming gateway ID (used as service_id)

    Returns:
        Dict with connection configuration for WorkerManager
    """
    # Get connection info (this already waits for server to be ready)
    connection_info = gateway_util.get_and_wait_for_connection_info(
        server_type=server_type
    )

    # Build stream config
    stream_config = {
        **connection_info,
        'service_id': service_id,
    }

    # Add Redis-specific batching defaults if applicable
    # These will be auto-optimized by WorkerManager based on camera count
    if server_type.lower() == 'redis':
        stream_config.update({
            'pool_max_connections': 500,  # High connection pool for 1000+ cameras
            'enable_batching': True,
            'batch_size': 10,
            'batch_timeout': 0.01,
        })

    return stream_config