"""Module providing camera manager functionality for deployments."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class CameraLocationInfo:
    """
    Camera location info data class for detailed location information.
    
    Attributes:
        street_address: Street address of the location
        city: City name
        state: State or province
        country: Country name
    """
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert location info to dictionary for API calls."""
        data = {}
        if self.street_address:
            data["streetAddress"] = self.street_address
        if self.city:
            data["city"] = self.city
        if self.state:
            data["state"] = self.state
        if self.country:
            data["country"] = self.country
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CameraLocationInfo":
        """Create CameraLocationInfo instance from API response data."""
        return cls(
            street_address=data.get("streetAddress"),
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country")
        )


@dataclass
class CameraLocationConfig:
    """
    Camera location configuration data class.
    
    Attributes:
        location_name: Name of the camera location
        location_info: Detailed location information
        account_number: Account number for the location
        id: Unique identifier for the location
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    location_name: str
    location_info: Optional[CameraLocationInfo] = None
    account_number: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert location config to dictionary for API calls."""
        if not self.location_name or not self.location_name.strip():
            raise ValueError("Location name is required")
        
        data = {
            "locationName": self.location_name
        }
        
        if self.account_number:
            data["accountNumber"] = self.account_number
        if self.location_info:
            data["locationInfo"] = self.location_info.to_dict()
        if self.id:
            data["_id"] = self.id
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CameraLocationConfig":
        """Create CameraLocationConfig instance from API response data."""
        location_info_data = data.get("locationInfo")
        location_info = CameraLocationInfo.from_dict(location_info_data) if location_info_data else None
        
        return cls(
            id=data.get("_id") or data.get("id") or data.get("ID"),
            location_name=data.get("locationName") or data.get("name") or "",
            location_info=location_info,
            account_number=data.get("accountNumber"),
            created_at=data.get("createdAt") or data.get("CreatedAt"),
            updated_at=data.get("updatedAt") or data.get("UpdatedAt")
        )


@dataclass
class StreamSettings:
    """
    Stream settings data class for camera configurations.

    Attributes:
        aspect_ratio: Aspect ratio of the camera (e.g., "16:9", "4:3")
        video_quality: Video quality setting (0-100)
        height: Video height in pixels
        width: Video width in pixels
        fps: Frames per second
        make: Camera make/manufacturer (optional)
        model: Camera model (optional)
        streaming_fps: Streaming FPS (optional, can differ from recording fps)
    """

    aspect_ratio: str
    video_quality: int
    height: int
    width: int
    fps: int
    make: Optional[str] = None
    model: Optional[str] = None
    streaming_fps: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert the stream settings to a dictionary for API calls."""
        data = {
            "aspectRatio": self.aspect_ratio,
            "videoQuality": self.video_quality,
            "height": self.height,
            "width": self.width,
            "fps": self.fps,
        }
        
        if self.make:
            data["make"] = self.make
        if self.model:
            data["model"] = self.model
        if self.streaming_fps:
            data["streamingFPS"] = self.streaming_fps
            
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "StreamSettings":
        """Create a StreamSettings instance from API response data."""
        return cls(
            aspect_ratio=data.get("aspectRatio", ""),
            video_quality=data.get("videoQuality", 0),
            height=data.get("height", 0),
            width=data.get("width", 0),
            fps=data.get("fps", 0),
            make=data.get("make"),
            model=data.get("model"),
            streaming_fps=data.get("streamingFPS"),
        )


@dataclass
class CameraGroupConfig:
    """
    Camera group data class for managing collections of cameras with shared settings.

    Attributes:
        camera_group_name: Name of the camera group
        streaming_gateway_id: ID of the streaming gateway this group belongs to
        default_stream_settings: Default stream settings for cameras in this group
        account_number: Account number for the camera group
        location_id: ID of the location (optional)
        id: Unique identifier for the camera group (MongoDB ObjectID)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    camera_group_name: str
    streaming_gateway_id: str
    default_stream_settings: StreamSettings
    account_number: Optional[str] = None
    location_id: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert the camera group to a dictionary for API calls."""
        if not self.camera_group_name or not self.camera_group_name.strip():
            raise ValueError("Camera group name is required")
        if not self.streaming_gateway_id:
            raise ValueError("Streaming gateway ID is required")
        if not self.default_stream_settings:
            raise ValueError("Default stream settings are required")
            
        data = {
            "cameraGroupName": self.camera_group_name,
            "streamingGatewayId": self.streaming_gateway_id,
            "defaultStreamSettings": self.default_stream_settings.to_dict(),
        }
        
        if self.account_number:
            data["accountNumber"] = self.account_number
        if self.location_id:
            data["locationId"] = self.location_id
        if self.id:
            data["_id"] = self.id
            
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "CameraGroupConfig":
        """Create a CameraGroup instance from API response data."""
        default_settings_data = data.get("defaultStreamSettings", {})
        default_settings = StreamSettings.from_dict(default_settings_data) if default_settings_data else None
        
        return cls(
            id=data.get("_id") or data.get("id") or data.get("ID"),
            camera_group_name=data.get("cameraGroupName") or data.get("name") or data.get("Name") or "",
            streaming_gateway_id=data.get("streamingGatewayId") or data.get("idService") or data.get("IDService") or "",
            default_stream_settings=default_settings,
            account_number=data.get("accountNumber"),
            location_id=data.get("locationId"),
            created_at=data.get("createdAt") or data.get("CreatedAt"),
            updated_at=data.get("updatedAt") or data.get("UpdatedAt"),
        )


@dataclass
class CameraConfig:
    """
    Camera configuration data class.

    Attributes:
        id: Unique identifier for the camera config (MongoDB ObjectID)
        id_service: Deployment ID this camera config belongs to (MongoDB ObjectID)
        camera_group_id: ID of the camera group this camera belongs to
        is_stream_url: Whether the stream URL is a valid URL
        camera_name: Name/identifier for the camera
        stream_url: URL for the camera stream
        custom_stream_settings: Custom stream settings that override group defaults
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    camera_name: str
    camera_group_id: str
    protocol_type: str
    camera_feed_path: Optional[str] = None
    simulation_video_path: Optional[str] = None
    custom_stream_settings: Optional[Dict] = None
    account_number: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_stream_url: bool = False
    stream_url: Optional[str] = None  # Legacy field for backward compatibility

    def __post_init__(self):
        if self.custom_stream_settings is None:
            self.custom_stream_settings = {}

    def to_dict(self) -> Dict:
        """Convert the camera config to a dictionary for API calls."""
        if not self.camera_name or not self.camera_name.strip():
            raise ValueError("Camera name is required")
        if not self.camera_group_id:
            raise ValueError("Camera group ID is required")
        if not self.protocol_type:
            raise ValueError("Protocol type is required")
        if self.protocol_type not in ["RTSP", "IP", "FILE"]:
            raise ValueError("Protocol type must be RTSP, IP, or FILE")
            
        data = {
            "cameraName": self.camera_name,
            "cameraGroupId": self.camera_group_id,
            "protocolType": self.protocol_type,
        }
        
        if self.account_number:
            data["accountNumber"] = self.account_number
        if self.camera_feed_path:
            data["cameraFeedPath"] = self.camera_feed_path
        if self.simulation_video_path:
            data["simulationVideoPath"] = self.simulation_video_path
        if self.custom_stream_settings:
            data["customStreamSettings"] = self.custom_stream_settings
        if self.id:
            data["_id"] = self.id
            
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "CameraConfig":
        """Create a CameraConfig instance from API response data."""
        camera_group_id = (
            data.get("CameraGroupID")
            or data.get("cameraGroupId")
            or data.get("groupId")
            or data.get("GroupId")
        )

        instance = cls(
            id=data.get("ID") or data.get("id") or data.get("_id"),
            camera_group_id=camera_group_id,
            camera_name=data.get("CameraName") or data.get("cameraName") or "",
            protocol_type=data.get("protocolType") or data.get("ProtocolType") or "RTSP",
            camera_feed_path=data.get("cameraFeedPath") or data.get("CameraFeedPath"),
            simulation_video_path=data.get("simulationVideoPath") or data.get("SimulationVideoPath"),
            custom_stream_settings=data.get("CustomStreamSettings") or data.get("customStreamSettings"),
            account_number=data.get("accountNumber") or data.get("AccountNumber"),
            created_at=data.get("CreatedAt") or data.get("createdAt"),
            updated_at=data.get("UpdatedAt") or data.get("updatedAt"),
            stream_url=data.get("StreamURL") or data.get("streamUrl") or data.get("cameraFeedPath"),  # For backward compatibility
            is_stream_url=data.get("IsStreamURL") or data.get("isStreamURL") or data.get("isStreamUrl") or True,
        )

        # Emit a debug diagnostic if camera_group_id could not be parsed
        if instance.camera_group_id in (None, ""):
            try:
                logging.debug(
                    "CameraConfig.from_dict: missing camera_group_id in payload keys=%s",
                    list(data.keys()),
                )
            except Exception:
                pass

        return instance

    def get_effective_stream_settings(
        self, group_defaults: StreamSettings
    ) -> StreamSettings:
        """
        Get the effective stream settings by merging group defaults with custom overrides.

        Args:
            group_defaults: Default stream settings from the camera group

        Returns:
            StreamSettings with effective values
        """
        # Start with group defaults
        effective = asdict(group_defaults)

        # Override with custom settings (convert camelCase to snake_case)
        custom_mapping = {
            "aspectRatio": "aspect_ratio",
            "videoQuality": "video_quality",
            "height": "height",
            "width": "width",
            "fps": "fps",
        }

        for api_key, attr_name in custom_mapping.items():
            if api_key in self.custom_stream_settings and self.custom_stream_settings[api_key]:
                effective[attr_name] = self.custom_stream_settings[api_key]

        return StreamSettings(**effective)


class Camera:
    """
    Camera instance class for managing individual camera configurations.

    This class represents a single camera and provides methods to manage
    its configuration, stream settings, and operational status.

    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.camera_manager import Camera, CameraConfig

        session = Session(account_number="...", access_key="...", secret_key="...")

        # Create camera config
        config = CameraConfig(
            camera_name="entrance_cam_01",
            stream_url="rtsp://192.168.1.100:554/stream1",
            camera_group_id="group_id_123",
            custom_stream_settings={"videoQuality": 90}
        )

        # Create camera instance
        camera = Camera(session, config)

        # Save to backend
        result, error, message = camera.save(service_id="deployment_id")
        if not error:
            print(f"Camera created with ID: {camera.id}")

        # Update configuration
        camera.stream_url = "rtsp://192.168.1.101:554/stream1"
        result, error, message = camera.update()
        ```
    """

    def __init__(self, session, config: CameraConfig = None, camera_id: str = None):
        """
        Initialize a Camera instance.

        Args:
            session: Session object containing RPC client for API communication
            config: CameraConfig object (for new cameras)
            camera_id: ID of existing camera to load (mutually exclusive with config)
        """
        if not config and not camera_id:
            raise ValueError("Either config or camera_id must be provided")

        self.session = session
        self.rpc = session.rpc

        if camera_id:
            # Load existing camera
            self.config = None
            self._load_from_id(camera_id)
        else:
            # New camera from config
            self.config = config

    @property
    def id(self) -> Optional[str]:
        """Get the camera ID."""
        return self.config.id if self.config else None

    @property
    def camera_name(self) -> str:
        """Get the camera name."""
        return self.config.camera_name if self.config else ""

    @camera_name.setter
    def camera_name(self, value: str):
        """Set the camera name."""
        if self.config:
            self.config.camera_name = value

    @property
    def stream_url(self) -> str:
        """Get the camera stream URL."""
        return self.get_stream_url()

    @stream_url.setter
    def stream_url(self, value: str):
        """Set the camera stream URL."""
        if self.config:
            self.config.stream_url = value

    @property
    def is_stream_url(self) -> bool:
        """Get whether the camera stream URL is a valid URL."""
        return self.config.is_stream_url if self.config else False

    @is_stream_url.setter
    def is_stream_url(self, value: bool):
        """Set whether the camera stream URL is a valid URL."""
        if self.config:
            self.config.is_stream_url = value

    @property
    def camera_group_id(self) -> str:
        """Get the camera group ID."""
        return self.config.camera_group_id if self.config else ""

    @camera_group_id.setter
    def camera_group_id(self, value: str):
        """Set the camera group ID."""
        if self.config:
            self.config.camera_group_id = value

    @property
    def custom_stream_settings(self) -> Dict:
        """Get the custom stream settings."""
        return self.config.custom_stream_settings if self.config else {}

    @custom_stream_settings.setter
    def custom_stream_settings(self, value: Dict):
        """Set the custom stream settings."""
        if self.config:
            self.config.custom_stream_settings = value

    def _load_from_id(self, camera_id: str):
        """Load camera configuration from backend by ID."""
        path = f"/v1/inference/get_camera_stream/{camera_id}"
        resp = self.rpc.get(path=path)

        if resp and resp.get("success"):
            data = resp.get("data")
            if data:
                self.config = CameraConfig.from_dict(data)
            else:
                raise ValueError(f"No data found for camera ID: {camera_id}")
        else:
            error_msg = resp.get("message") if resp else "No response received"
            raise ValueError(f"Failed to load camera: {error_msg}")

    def save(self, account_number: str = None) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Save the camera configuration to the backend (create new).

        Args:
            account_number: The account number to associate with the camera

        Returns:
            tuple: (result, error, message)
        """
        if not self.config:
            return None, "No configuration to save", "Invalid state"

        if self.id:
            return None, "Camera already exists, use update() instead", "Already exists"

        if account_number:
            self.config.account_number = account_number

        if not self.config.account_number:
            return None, "Account number is required", "Missing account number"

        # Validate camera config
        is_valid, validation_error = self._validate_camera_config()
        if not is_valid:
            return None, validation_error, "Validation failed"

        path = "/v1/inference/create_camera_stream"
        payload = self.config.to_dict()

        resp = self.rpc.post(path=path, payload=payload)

        if resp and resp.get("success"):
            result = resp.get("data")
            if result and "id" in result:
                self.config.id = result["id"]
            return result, None, "Camera created successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to create camera"

    def update(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update the camera configuration in the backend.

        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Camera must be saved before updating", "Invalid state"

        path = f"/v1/inference/update_camera_stream/{self.config.id}"
        payload = {
            "cameraName": self.config.camera_name,
            "protocolType": self.config.protocol_type
        }
        
        if self.config.camera_feed_path:
            payload["cameraFeedPath"] = self.config.camera_feed_path
        if self.config.simulation_video_path:
            payload["simulationVideoPath"] = self.config.simulation_video_path
        if self.config.custom_stream_settings:
            payload["customStreamSettings"] = self.config.custom_stream_settings

        resp = self.rpc.put(path=path, payload=payload)

        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera updated successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to update camera"

    def delete(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete the camera from the backend.

        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Camera must be saved before deleting", "Invalid state"

        path = f"/v1/inference/delete_camera_stream/{self.config.id}"

        resp = self.rpc.delete(path=path)

        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera deleted successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to delete camera"

    def get_stream_url(self) -> str:
        """Get the camera stream URL."""
        if not self.config.id:
            return ""
        if self.config.is_stream_url:
            return self.config.stream_url

        resp = self.rpc.get(f"/v1/inference/get_stream_url/{self.config.id}")
        if resp and resp.get("success") and resp.get("data"):
            self.config.stream_url = resp.get("data", {}).get("streamUrl")
            self.config.is_stream_url = True

        return self.config.stream_url

    def get_effective_stream_settings(
        self, group_defaults: StreamSettings
    ) -> StreamSettings:
        """
        Get the effective stream settings by merging group defaults with custom overrides.

        Args:
            group_defaults: Default stream settings from the camera group

        Returns:
            StreamSettings with effective values
        """
        if self.config:
            return self.config.get_effective_stream_settings(group_defaults)
        return group_defaults

    def refresh(self):
        """Refresh the camera configuration from the backend."""
        if self.config and self.config.id:
            self._load_from_id(self.config.id)

    def _validate_camera_config(self) -> Tuple[bool, str]:
        """
        Validate camera configuration data.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.config:
            return False, "No configuration to validate"

        if not self.config.camera_name or not self.config.camera_name.strip():
            return False, "Camera name is required"

        if not self.config.protocol_type:
            return False, "Protocol type is required"
        
        if self.config.protocol_type not in ["RTSP", "IP", "FILE"]:
            return False, "Protocol type must be RTSP, IP, or FILE"
        
        # Validate protocol-specific requirements
        if self.config.protocol_type == "FILE" and not self.config.simulation_video_path:
            return False, "Simulation video path is required for FILE protocol type"
        
        if self.config.protocol_type in ["RTSP", "IP"] and not self.config.camera_feed_path:
            return False, "Camera feed path is required for RTSP/IP protocol type"

        if not self.config.camera_group_id:
            return False, "Camera group ID is required"

        # Validate custom stream settings if provided
        if self.config.custom_stream_settings:
            custom = self.config.custom_stream_settings

            if "aspectRatio" in custom and custom["aspectRatio"] not in [
                "16:9",
                "4:3",
                "1:1",
            ]:
                return False, "Custom aspect ratio must be one of: 16:9, 4:3, 1:1"

            if "videoQuality" in custom and not (0 <= custom["videoQuality"] <= 100):
                return False, "Custom video quality must be between 0 and 100"

            if "height" in custom and custom["height"] <= 0:
                return False, "Custom height must be greater than 0"

            if "width" in custom and custom["width"] <= 0:
                return False, "Custom width must be greater than 0"

            if "fps" in custom and custom["fps"] <= 0:
                return False, "Custom FPS must be greater than 0"

        return True, ""


class CameraGroup:
    """
    Camera group instance class for managing individual camera groups and their cameras.

    This class represents a single camera group and provides methods to manage
    its configuration, cameras, and operational status.

    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.camera_manager import CameraGroup, CameraGroup, StreamSettings

        session = Session(account_number="...", access_key="...", secret_key="...")

        # Create camera group config
        default_settings = StreamSettings(
            aspect_ratio="16:9",
            video_quality=80,
            height=1080,
            width=1920,
            fps=30,
            make="Hikvision",
            model="DS-2CD2143G0",
            streaming_fps=30
        )

        group_config = CameraGroupConfig(
            camera_group_name="Indoor Cameras",
            streaming_gateway_id="gateway123",
            default_stream_settings=default_settings,
            account_number="ACC-123",
            location_id="loc123"
        )

        # Create camera group instance
        camera_group = CameraGroup(session, group_config)

        # Save to backend
        result, error, message = camera_group.save(service_id="deployment_id")
        if not error:
            print(f"Camera group created with ID: {camera_group.id}")

        # Add cameras to the group
        camera_config = CameraConfig(
            camera_name="entrance_cam_01",
            stream_url="rtsp://192.168.1.100:554/stream1",
            camera_group_id=camera_group.id
        )
        camera, error, message = camera_group.add_camera(camera_config)
        ```
    """

    def __init__(self, session, config: CameraGroupConfig = None, group_id: str = None):
        """
        Initialize a CameraGroup.

        Args:
            session: Session object containing RPC client for API communication
            config: CameraGroup object (for new groups)
            group_id: ID of existing group to load (mutually exclusive with config)
        """
        if not config and not group_id:
            raise ValueError("Either config or group_id must be provided")

        self.session = session
        self.rpc = session.rpc
        self._cameras = []  # Cache for cameras in this group

        if group_id:
            # Load existing group
            self.config = None
            self._load_from_id(group_id)
        else:
            # New group from config
            self.config = config

    @property
    def id(self) -> Optional[str]:
        """Get the group ID."""
        return self.config.id if self.config else None

    @property
    def camera_group_name(self) -> str:
        """Get the camera group name."""
        return self.config.camera_group_name if self.config else ""

    @camera_group_name.setter
    def camera_group_name(self, value: str):
        """Set the camera group name."""
        if self.config:
            self.config.camera_group_name = value
    
    @property
    def name(self) -> str:
        """Get the group name (alias for camera_group_name)."""
        return self.camera_group_name

    @name.setter
    def name(self, value: str):
        """Set the group name (alias for camera_group_name)."""
        self.camera_group_name = value

    @property
    def streaming_gateway_id(self) -> str:
        """Get the streaming gateway ID."""
        return self.config.streaming_gateway_id if self.config else ""

    @streaming_gateway_id.setter
    def streaming_gateway_id(self, value: str):
        """Set the streaming gateway ID."""
        if self.config:
            self.config.streaming_gateway_id = value
    
    @property
    def location_id(self) -> Optional[str]:
        """Get the location ID."""
        return self.config.location_id if self.config else None

    @location_id.setter
    def location_id(self, value: str):
        """Set the location ID."""
        if self.config:
            self.config.location_id = value
    
    @property
    def account_number(self) -> Optional[str]:
        """Get the account number."""
        return self.config.account_number if self.config else None

    @account_number.setter
    def account_number(self, value: str):
        """Set the account number."""
        if self.config:
            self.config.account_number = value

    @property
    def default_stream_settings(self) -> Optional[StreamSettings]:
        """Get the default stream settings."""
        return self.config.default_stream_settings if self.config else None

    @default_stream_settings.setter
    def default_stream_settings(self, value: StreamSettings):
        """Set the default stream settings."""
        if self.config:
            self.config.default_stream_settings = value

    @property
    def cameras(self) -> List["Camera"]:
        """Get all cameras in this group."""
        return self._cameras

    def _load_from_id(self, group_id: str):
        """Load camera group configuration from backend by ID."""
        path = f"/v1/inference/get_camera_group/{group_id}"
        resp = self.rpc.get(path=path)

        if resp and resp.get("success"):
            data = resp.get("data")
            if data:
                self.config = CameraGroupConfig.from_dict(data)
            else:
                raise ValueError(f"No data found for camera group ID: {group_id}")
        else:
            error_msg = resp.get("message") if resp else "No response received"
            raise ValueError(f"Failed to load camera group: {error_msg}")

    def save(self, account_number: str = None) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Save the camera group configuration to the backend (create new).

        Args:
            account_number: The account number to associate with the camera group

        Returns:
            tuple: (result, error, message)
        """
        if not self.config:
            return None, "No configuration to save", "Invalid state"

        if self.id:
            return (
                None,
                "Camera group already exists, use update() instead",
                "Already exists",
            )

        if account_number:
            self.config.account_number = account_number

        if not self.config.account_number:
            return None, "Account number is required", "Missing account number"

        # Validate camera group
        is_valid, validation_error = self._validate_camera_group()
        if not is_valid:
            return None, validation_error, "Validation failed"

        path = "/v1/inference/create_camera_group"
        payload = self.config.to_dict()

        resp = self.rpc.post(path=path, payload=payload)

        if resp and resp.get("success"):
            result = resp.get("data")
            if result and "id" in result:
                self.config.id = result["id"]
            return result, None, "Camera group created successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to create camera group"

    def update(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update the camera group configuration in the backend.

        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Camera group must be saved before updating", "Invalid state"

        path = f"/v1/inference/update_camera_group/{self.config.id}"
        payload = {
            "cameraGroupName": self.config.camera_group_name,
            "defaultStreamSettings": self.config.default_stream_settings.to_dict()
        }
        
        if self.config.location_id:
            payload["locationId"] = self.config.location_id

        resp = self.rpc.put(path=path, payload=payload)

        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera group updated successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to update camera group"

    def delete(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete the camera group from the backend.

        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Camera group must be saved before deleting", "Invalid state"

        path = f"/v1/inference/delete_camera_group/{self.config.id}"

        resp = self.rpc.delete(path=path)

        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera group deleted successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to delete camera group"

    def add_camera(
        self, camera_config: CameraConfig
    ) -> Tuple[Optional["Camera"], Optional[str], str]:
        """
        Add a camera to this camera group.

        Args:
            camera_config: CameraConfig object containing the camera configuration

        Returns:
            tuple: (camera_instance, error, message)
        """
        if not self.config or not self.config.id:
            return (
                None,
                "Camera group must be saved before adding cameras",
                "Invalid state",
            )

        if not isinstance(camera_config, CameraConfig):
            return None, "Config must be a CameraConfig instance", "Invalid config type"

        # Set the camera group ID
        camera_config.camera_group_id = self.config.id
        camera_config.account_number = self.config.account_number

        # Create camera instance
        camera_instance = Camera(self.session, camera_config)

        # Save to backend
        result, error, message = camera_instance.save()

        if error:
            return None, error, message

        # Add to local cache
        self._cameras.append(camera_instance)

        return camera_instance, None, message

    def get_cameras(
        self, page: int = 1, limit: int = 10, search: str = None
    ) -> Tuple[Optional[List["Camera"]], Optional[str], str]:
        """
        Get all cameras in this camera group.

        Args:
            page: Page number for pagination
            limit: Items per page
            search: Optional search term

        Returns:
            tuple: (camera_instances, error, message)
        """
        if not self.config or not self.config.id:
            return (
                None,
                "Camera group must be saved before getting cameras",
                "Invalid state",
            )

        if not self.config.account_number:
            return None, "Account number is required", "Missing account number"

        path = f"/v1/inference/camera_streams_by_acc_number/{self.config.account_number}"
        params = {"page": page, "limit": limit, "groupId": self.config.id}
        if search:
            params["search"] = search

        resp = self.rpc.get(path=path, params=params)

        if resp and resp.get("success"):
            result = resp.get("data")
            if result and "items" in result:
                try:
                    camera_instances = []
                    for config_data in result["items"]:
                        try:
                            camera_config = CameraConfig.from_dict(config_data)
                            if camera_config.camera_group_id != self.config.id:
                                continue
                            camera_instance = Camera(self.session, camera_config)
                            camera_instances.append(camera_instance)
                        except Exception as e:
                            logging.warning(f"Failed to parse camera config data: {e}")
                            continue

                    # Update local cache
                    self._cameras = camera_instances
                    return camera_instances, None, "Cameras retrieved successfully"
                except Exception as e:
                    return (
                        None,
                        f"Failed to parse camera configs: {str(e)}",
                        "Parse error",
                    )

            return [], None, "No cameras found"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to retrieve cameras"

    def remove_camera(
        self, camera_id: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Remove a camera from this camera group.

        Args:
            camera_id: ID of the camera to remove

        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"

        path = f"/v1/inference/delete_camera_stream/{camera_id}"
        resp = self.rpc.delete(path=path)

        if resp and resp.get("success"):
            result = resp.get("data")
            # Remove from local cache
            self._cameras = [cam for cam in self._cameras if cam.id != camera_id]
            return result, None, "Camera removed successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to remove camera"

    def refresh(self):
        """Refresh the camera group configuration and cameras from the backend."""
        if self.config and self.config.id:
            self._load_from_id(self.config.id)
            # Refresh cameras list
            self.get_cameras()

    def _validate_camera_group(self) -> Tuple[bool, str]:
        """
        Validate camera group data.

        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.config:
            return False, "No configuration to validate"

        if not self.config.camera_group_name or not self.config.camera_group_name.strip():
            return False, "Camera group name is required"

        if not self.config.streaming_gateway_id:
            return False, "Streaming gateway ID is required"
        
        if not self.config.default_stream_settings:
            return False, "Default stream settings are required"

        # Validate stream settings
        settings = self.config.default_stream_settings
        if settings.aspect_ratio not in ["16:9", "4:3", "1:1"]:
            return False, "Aspect ratio must be one of: 16:9, 4:3, 1:1"

        if not (0 <= settings.video_quality <= 100):
            return False, "Video quality must be between 0 and 100"

        if settings.height <= 0:
            return False, "Height must be greater than 0"

        if settings.width <= 0:
            return False, "Width must be greater than 0"

        if settings.fps <= 0:
            return False, "FPS must be greater than 0"
        
        if settings.streaming_fps and settings.streaming_fps <= 0:
            return False, "Streaming FPS must be greater than 0"

        return True, ""


class CameraLocation:
    """
    Camera location instance class for managing individual camera locations.
    
    This class represents a single camera location and provides methods to manage
    its configuration and operational status.
    
    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.camera_manager import CameraLocation, CameraLocationConfig, CameraLocationInfo
        
        session = Session(account_number="...", access_key="...", secret_key="...")
        
        # Create location info
        location_info = CameraLocationInfo(
            street_address="123 Main St",
            city="NYC",
            state="NY",
            country="USA"
        )
        
        # Create location config
        config = CameraLocationConfig(
            location_name="HQ Building",
            location_info=location_info,
            account_number="ACC-123"
        )
        
        # Create location instance
        location = CameraLocation(session, config)
        
        # Save to backend
        result, error, message = location.save()
        if not error:
            print(f"Location created with ID: {location.id}")
        
        # Update configuration
        location.location_name = "HQ North Wing"
        result, error, message = location.update()
        ```
    """
    
    def __init__(self, session, config: CameraLocationConfig = None, location_id: str = None):
        """
        Initialize a CameraLocation instance.
        
        Args:
            session: Session object containing RPC client for API communication
            config: CameraLocationConfig object (for new locations)
            location_id: ID of existing location to load (mutually exclusive with config)
        """
        if not config and not location_id:
            raise ValueError("Either config or location_id must be provided")
        
        self.session = session
        self.rpc = session.rpc
        
        if location_id:
            # Load existing location
            self.config = None
            self._load_from_id(location_id)
        else:
            # New location from config
            self.config = config
    
    @property
    def id(self) -> Optional[str]:
        """Get the location ID."""
        return self.config.id if self.config else None
    
    @property
    def location_name(self) -> str:
        """Get the location name."""
        return self.config.location_name if self.config else ""
    
    @location_name.setter
    def location_name(self, value: str):
        """Set the location name."""
        if self.config:
            self.config.location_name = value
    
    @property
    def location_info(self) -> Optional[CameraLocationInfo]:
        """Get the location info."""
        return self.config.location_info if self.config else None
    
    @location_info.setter
    def location_info(self, value: CameraLocationInfo):
        """Set the location info."""
        if self.config:
            self.config.location_info = value
    
    @property
    def account_number(self) -> Optional[str]:
        """Get the account number."""
        return self.config.account_number if self.config else None
    
    @account_number.setter
    def account_number(self, value: str):
        """Set the account number."""
        if self.config:
            self.config.account_number = value
    
    def _load_from_id(self, location_id: str):
        """Load camera location configuration from backend by ID."""
        path = f"/v1/inference/get_location/{location_id}"
        resp = self.rpc.get(path=path)
        
        if resp and resp.get("success"):
            data = resp.get("data")
            if data:
                self.config = CameraLocationConfig.from_dict(data)
            else:
                raise ValueError(f"No data found for location ID: {location_id}")
        else:
            error_msg = resp.get("message") if resp else "No response received"
            raise ValueError(f"Failed to load location: {error_msg}")
    
    def save(self, account_number: str = None) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Save the location configuration to the backend (create new).
        
        Args:
            account_number: The account number to associate with the location
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config:
            return None, "No configuration to save", "Invalid state"
        
        if self.id:
            return None, "Location already exists, use update() instead", "Already exists"
        
        if account_number:
            self.config.account_number = account_number
        
        if not self.config.account_number:
            return None, "Account number is required", "Missing account number"
        
        path = "/v1/inference/create_location"
        payload = self.config.to_dict()
        
        resp = self.rpc.post(path=path, payload=payload)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            if result and "id" in result:
                self.config.id = result["id"]
            return result, None, "Camera location created successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to create camera location"
    
    def update(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update the location configuration in the backend.
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Location must be saved before updating", "Invalid state"
        
        path = f"/v1/inference/update_location/{self.config.id}"
        payload = {
            "locationName": self.config.location_name
        }
        
        if self.config.location_info:
            payload["locationInfo"] = self.config.location_info.to_dict()
        
        resp = self.rpc.put(path=path, payload=payload)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera location updated successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to update camera location"
    
    def delete(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete the location from the backend.
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Location must be saved before deleting", "Invalid state"
        
        path = f"/v1/inference/delete_location/{self.config.id}"
        
        resp = self.rpc.delete(path=path)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Camera location deleted successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to delete camera location"
    
    def refresh(self):
        """Refresh the location configuration from the backend."""
        if self.config and self.config.id:
            self._load_from_id(self.config.id)


class CameraManager:
    """
    Camera manager client for handling camera groups and configurations in deployments.

    This class provides methods to create, read, update, and delete camera groups and
    camera configurations associated with deployments. It offers a streamlined flow
    for managing camera infrastructure.

    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.camera_manager import CameraManager, CameraGroup, CameraConfig, StreamSettings

        session = Session(account_number="...", access_key="...", secret_key="...")
        camera_manager = CameraManager(session, service_id="...")

        # Create a camera group with default settings
        default_settings = StreamSettings(
            aspect_ratio="16:9",
            video_quality=80,
            height=1080,
            width=1920,
            fps=30,
            make="Hikvision",
            model="DS-2CD2143G0",
            streaming_fps=30
        )

        group = CameraGroupConfig(
            camera_group_name="Indoor Cameras",
            streaming_gateway_id="gateway123",
            default_stream_settings=default_settings,
            account_number="ACC-123",
            location_id="loc123"
        )

        # Create the camera group
        camera_group, error, message = camera_manager.create_camera_group(group)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Camera group created: {camera_group.name}")

            # Add cameras to the group
            camera_config = CameraConfig(
                camera_name="main_entrance_cam",
                stream_url="rtsp://192.168.1.100:554/stream1",
                camera_group_id=camera_group.id,
                custom_stream_settings={"videoQuality": 90}
            )

            camera, error, message = camera_group.add_camera(camera_config)
            if not error:
                print(f"Camera added: {camera.camera_name}")
        ```
    """

    def __init__(self, session, service_id: str = None, account_number: str = None):
        """
        Initialize the CameraManager client.

        Args:
            session: Session object containing RPC client for API communication
            service_id: The ID of the deployment or the ID of the inference pipeline
            account_number: The account number for API calls
        """
        self.session = session
        self.rpc = session.rpc
        self.service_id = service_id
        self.account_number = account_number or getattr(session, 'account_number', None)

    def handle_response(
        self, response: Dict, success_message: str, failure_message: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """Handle API response and return standardized tuple."""
        if response and response.get("success"):
            result = response.get("data")
            error = None
            message = success_message
        else:
            result = None
            error = response.get("message") if response else "No response received"
            message = failure_message
        return result, error, message

    # Camera Location Management Methods
    
    def create_camera_location(self, config: CameraLocationConfig) -> Tuple[Optional['CameraLocation'], Optional[str], str]:
        """
        Create a new camera location.
        
        Args:
            config: CameraLocationConfig object containing the location configuration
            
        Returns:
            tuple: (camera_location, error, message)
        """
        if not isinstance(config, CameraLocationConfig):
            return None, "Config must be a CameraLocationConfig instance", "Invalid config type"
        
        # Create location instance
        location = CameraLocation(self.session, config)
        
        # Save to backend
        result, error, message = location.save(account_number=self.account_number)
        
        if error:
            return None, error, message
        
        return location, None, message
    
    def get_camera_location_by_id(self, location_id: str) -> Tuple[Optional['CameraLocation'], Optional[str], str]:
        """
        Get a camera location by its ID.
        
        Args:
            location_id: The ID of the camera location to retrieve
            
        Returns:
            tuple: (camera_location, error, message)
        """
        if not location_id:
            return None, "Location ID is required", "Invalid location ID"
        
        try:
            location = CameraLocation(self.session, location_id=location_id)
            return location, None, "Camera location retrieved successfully"
        except Exception as e:
            return None, str(e), "Failed to retrieve camera location"
    
    def get_camera_locations(self, page: int = 1, limit: int = 10) -> Tuple[Optional[List['CameraLocation']], Optional[str], str]:
        """
        Get all camera locations for the account.
        
        Args:
            page: Page number for pagination
            limit: Items per page
            
        Returns:
            tuple: (camera_locations, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"
        
        path = f"/v1/inference/locations_by_acc_number/{self.account_number}"
        params = {"page": page, "limit": limit} if page > 1 or limit != 10 else {}
            
        resp = self.rpc.get(path=path, params=params)
        
        result, error, message = self.handle_response(
            resp,
            "Camera locations retrieved successfully",
            "Failed to retrieve camera locations"
        )
        
        if error:
            return None, error, message
        
        if result:
            try:
                # Handle different response structures
                if isinstance(result, dict) and "data" in result:
                    location_data_list = result["data"]
                elif isinstance(result, dict) and "items" in result:
                    location_data_list = result["items"]
                elif isinstance(result, list):
                    location_data_list = result
                else:
                    location_data_list = []
                
                if not location_data_list:
                    return [], None, "No camera locations found"
                
                # Convert to CameraLocation instances
                camera_locations = []
                for location_data in location_data_list:
                    try:
                        config = CameraLocationConfig.from_dict(location_data)
                        location = CameraLocation(self.session, config)
                        camera_locations.append(location)
                    except Exception as e:
                        logging.warning(f"Failed to parse location data: {e}")
                        continue
                
                return camera_locations, None, message
            except Exception as e:
                return None, f"Failed to parse camera locations: {str(e)}", "Parse error"
        
        return [], None, message
    
    def get_camera_locations_paginated(self, page: int = 1, limit: int = 10) -> Tuple[Optional[List['CameraLocation']], Optional[str], str]:
        """
        Get paginated camera locations for the account.
        
        Args:
            page: Page number for pagination
            limit: Items per page
            
        Returns:
            tuple: (camera_locations, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"
        
        path = f"/v1/inference/all_locations_pag/{self.account_number}"
        params = {"page": page, "limit": limit}
            
        resp = self.rpc.get(path=path, params=params)
        
        result, error, message = self.handle_response(
            resp,
            "Camera locations retrieved successfully",
            "Failed to retrieve camera locations"
        )
        
        if error:
            return None, error, message
        
        if result:
            try:
                # Handle paginated response structure
                if isinstance(result, dict):
                    location_data_list = result.get("items", result.get("data", []))
                elif isinstance(result, list):
                    location_data_list = result
                else:
                    location_data_list = []
                
                # Convert to CameraLocation instances
                camera_locations = []
                for location_data in location_data_list:
                    try:
                        config = CameraLocationConfig.from_dict(location_data)
                        location = CameraLocation(self.session, config)
                        camera_locations.append(location)
                    except Exception as e:
                        logging.warning(f"Failed to parse location data: {e}")
                        continue
                
                return camera_locations, None, message
            except Exception as e:
                return None, f"Failed to parse camera locations: {str(e)}", "Parse error"
        
        return [], None, message
    
    def update_camera_location(self, location_id: str, config: CameraLocationConfig) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update an existing camera location.
        
        Args:
            location_id: The ID of the location to update
            config: CameraLocationConfig object with updated configuration
        
        Returns:
            tuple: (result, error, message)
        """
        if not location_id:
            return None, "Location ID is required", "Invalid location ID"
        
        if not isinstance(config, CameraLocationConfig):
            return None, "Config must be a CameraLocationConfig instance", "Invalid config type"
        
        path = f"/v1/inference/update_location/{location_id}"
        payload = {
            "locationName": config.location_name
        }
        
        if config.location_info:
            payload["locationInfo"] = config.location_info.to_dict()
        
        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp, "Camera location updated successfully", "Failed to update camera location"
        )
    
    def delete_camera_location(self, location_id: str) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete a camera location by its ID.
        
        Args:
            location_id: The ID of the location to delete
        
        Returns:
            tuple: (result, error, message)
        """
        if not location_id:
            return None, "Location ID is required", "Invalid location ID"
        
        path = f"/v1/inference/delete_location/{location_id}"
        resp = self.rpc.delete(path=path)
        
        return self.handle_response(
            resp, "Camera location deleted successfully", "Failed to delete camera location"
        )

    # Camera Stream Topic Management Methods
    
    def create_camera_stream_topic(
        self,
        camera_id: str,
        streaming_gateway_id: str,
        topic_name: str,
        topic_type: str,
        status: str,
        ip_address: str = None,
        port: int = None,
        app_deployment_id: str = None,
        consuming_app_deployment_ids: List[str] = None
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Create a camera stream topic.
        
        Args:
            camera_id: ID of the camera
            streaming_gateway_id: ID of the streaming gateway
            topic_name: Name of the topic
            topic_type: Type of topic (input|output)
            status: Status of the topic
            ip_address: IP address (optional)
            port: Port number (optional)
            app_deployment_id: App deployment ID for output topics (optional)
            consuming_app_deployment_ids: List of consuming app deployment IDs for input topics (optional)
        
        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"
        if not streaming_gateway_id:
            return None, "Streaming gateway ID is required", "Invalid streaming gateway ID"
        if not topic_name:
            return None, "Topic name is required", "Invalid topic name"
        if topic_type not in ["input", "output"]:
            return None, "Topic type must be 'input' or 'output'", "Invalid topic type"
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"
        
        path = "/v1/inference/create_camera_stream_topic"
        payload = {
            "accountNumber": self.account_number,
            "cameraId": camera_id,
            "streamingGatewayId": streaming_gateway_id,
            "topicName": topic_name,
            "topicType": topic_type,
            "status": status
        }
        
        if ip_address:
            payload["ipAddress"] = ip_address
        if port:
            payload["port"] = port
        if app_deployment_id:
            payload["appDeploymentId"] = app_deployment_id
        if consuming_app_deployment_ids:
            payload["consumingAppsDeploymentIds"] = consuming_app_deployment_ids
        
        resp = self.rpc.post(path=path, payload=payload)
        return self.handle_response(
            resp, "Camera stream topic created successfully", "Failed to create camera stream topic"
        )
    
    def append_consuming_app_deployment_id(
        self,
        camera_id: str,
        streaming_id: str,
        topic_type: str,
        app_deployment_id: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Append a consuming app deployment ID to an input topic.
        
        Args:
            camera_id: ID of the camera
            streaming_id: ID of the streaming gateway
            topic_type: Type of topic (should be 'input')
            app_deployment_id: App deployment ID to append
        
        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"
        if not streaming_id:
            return None, "Streaming ID is required", "Invalid streaming ID"
        if not topic_type:
            return None, "Topic type is required", "Invalid topic type"
        if not app_deployment_id:
            return None, "App deployment ID is required", "Invalid app deployment ID"
        
        path = "/v1/inference/append_consuming_app_deployment_id"
        payload = {
            "cameraId": camera_id,
            "streamingId": streaming_id,
            "topicType": topic_type,
            "appDeploymentId": app_deployment_id
        }
        
        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp, "Consuming app deployment ID appended successfully", "Failed to append consuming app deployment ID"
        )
    
    def update_topic_ip_and_port(
        self,
        camera_id: str,
        streaming_id: str,
        topic_type: str,
        ip_address: str,
        port: int
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update IP address and port on a camera stream topic.
        
        Args:
            camera_id: ID of the camera
            streaming_id: ID of the streaming gateway
            topic_type: Type of topic (input|output)
            ip_address: New IP address
            port: New port number
        
        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"
        if not streaming_id:
            return None, "Streaming ID is required", "Invalid streaming ID"
        if not topic_type:
            return None, "Topic type is required", "Invalid topic type"
        if not ip_address:
            return None, "IP address is required", "Invalid IP address"
        if not port or port <= 0:
            return None, "Valid port is required", "Invalid port"
        
        path = "/v1/inference/update_ip_and_port"
        payload = {
            "cameraId": camera_id,
            "streamingId": streaming_id,
            "topicType": topic_type,
            "ipAddress": ip_address,
            "port": port
        }
        
        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp, "Topic IP and port updated successfully", "Failed to update topic IP and port"
        )

    # Camera Group Management Methods

    def create_camera_group(
        self, group: CameraGroupConfig
    ) -> Tuple[Optional["CameraGroup"], Optional[str], str]:
        """
        Create a new camera group for a deployment.

        Args:
            group: CameraGroup object containing the group configuration

        Returns:
            tuple: (camera_group_instance, error, message)
                - camera_group_instance: CameraGroupInstance if successful, None otherwise
                - error: Error message if failed, None otherwise
                - message: Status message
        """
        if not isinstance(group, CameraGroupConfig):
            return None, "Group must be a CameraGroup instance", "Invalid group type"

        # Create camera group instance
        camera_group_instance = CameraGroup(self.session, group)

        # Save to backend
        result, error, message = camera_group_instance.save(account_number=self.account_number)

        if error:
            return None, error, message

        return camera_group_instance, None, message

    def get_camera_group_by_id(
        self, group_id: str
    ) -> Tuple[Optional["CameraGroup"], Optional[str], str]:
        """
        Get a camera group by its ID.

        Args:
            group_id: The ID of the camera group to retrieve

        Returns:
            tuple: (camera_group_instance, error, message)
        """
        if not group_id:
            return None, "Group ID is required", "Invalid group ID"

        try:
            camera_group_instance = CameraGroup(self.session, group_id=group_id)
            return camera_group_instance, None, "Camera group retrieved successfully"
        except Exception as e:
            return None, str(e), "Failed to retrieve camera group"

    def get_camera_groups(
        self, page: int = 1, limit: int = 10
    ) -> Tuple[Optional[List["CameraGroup"]], Optional[str], str]:
        """
        Get all camera groups for the account.

        Args:
            page: Page number for pagination
            limit: Items per page

        Returns:
            tuple: (camera_group_instances, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"

        path = f"/v1/inference/camera_groups_by_acc_number/{self.account_number}"
        params = {"page": page, "limit": limit} if page > 1 or limit != 10 else {}

        resp = self.rpc.get(path=path, params=params)

        result, error, message = self.handle_response(
            resp,
            "Camera groups retrieved successfully",
            "Failed to retrieve camera groups",
        )

        if error:
            return None, error, message

        if result:
            try:
                # Handle different response structures
                if isinstance(result, dict) and "data" in result:
                    group_data_list = result["data"]
                elif isinstance(result, dict) and "items" in result:
                    group_data_list = result["items"]
                elif isinstance(result, list):
                    group_data_list = result
                else:
                    group_data_list = []
                
                if not group_data_list:
                    return [], None, "No camera groups found"
                
                camera_group_instances = []
                for group_data in group_data_list:
                    try:
                        group_config = CameraGroupConfig.from_dict(group_data)
                        camera_group_instance = CameraGroup(self.session, group_config)
                        camera_group_instances.append(camera_group_instance)
                    except Exception as e:
                        logging.warning(f"Failed to parse camera group data: {e}")
                        continue

                logging.debug(
                    "get_camera_groups: account_number=%s page=%s limit=%s -> groups=%s",
                    self.account_number,
                    page,
                    limit,
                    len(camera_group_instances),
                )
                return camera_group_instances, None, message
            except Exception as e:
                return None, f"Failed to parse camera groups: {str(e)}", "Parse error"

        return [], None, message
    
    def get_camera_groups_paginated(
        self, page: int = 1, limit: int = 10
    ) -> Tuple[Optional[List["CameraGroup"]], Optional[str], str]:
        """
        Get paginated camera groups for the account.

        Args:
            page: Page number for pagination
            limit: Items per page

        Returns:
            tuple: (camera_group_instances, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"

        path = f"/v1/inference/all_camera_groups_pag/{self.account_number}"
        params = {"page": page, "limit": limit}

        resp = self.rpc.get(path=path, params=params)

        result, error, message = self.handle_response(
            resp,
            "Camera groups retrieved successfully",
            "Failed to retrieve camera groups",
        )

        if error:
            return None, error, message

        if result:
            try:
                # Handle paginated response structure
                if isinstance(result, dict):
                    group_data_list = result.get("items", result.get("data", []))
                elif isinstance(result, list):
                    group_data_list = result
                else:
                    group_data_list = []
                
                camera_group_instances = []
                for group_data in group_data_list:
                    try:
                        group_config = CameraGroupConfig.from_dict(group_data)
                        camera_group_instance = CameraGroup(self.session, group_config)
                        camera_group_instances.append(camera_group_instance)
                    except Exception as e:
                        logging.warning(f"Failed to parse camera group data: {e}")
                        continue

                return camera_group_instances, None, message
            except Exception as e:
                return None, f"Failed to parse camera groups: {str(e)}", "Parse error"

        return [], None, message

    def update_camera_group(
        self, group_id: str, group: CameraGroupConfig
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update an existing camera group.

        Args:
            group_id: The ID of the camera group to update
            group: CameraGroup object with updated configuration

        Returns:
            tuple: (result, error, message)
        """
        if not group_id:
            return None, "Group ID is required", "Invalid group ID"

        if not isinstance(group, CameraGroupConfig):
            return None, "Group must be a CameraGroup instance", "Invalid group type"

        path = f"/v1/inference/update_camera_group/{group_id}"
        payload = {
            "cameraGroupName": group.camera_group_name,
            "defaultStreamSettings": group.default_stream_settings.to_dict()
        }
        
        if group.location_id:
            payload["locationId"] = group.location_id

        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp, "Camera group updated successfully", "Failed to update camera group"
        )

    def delete_camera_group(
        self, group_id: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete a camera group by its ID.

        Args:
            group_id: The ID of the camera group to delete

        Returns:
            tuple: (result, error, message)
        """
        if not group_id:
            return None, "Group ID is required", "Invalid group ID"

        path = f"/v1/inference/delete_camera_group/{group_id}"
        resp = self.rpc.delete(path=path)

        return self.handle_response(
            resp, "Camera group deleted successfully", "Failed to delete camera group"
        )

    # Camera Management Methods

    def create_camera(
        self, camera_config: CameraConfig
    ) -> Tuple[Optional["Camera"], Optional[str], str]:
        """
        Create a new camera configuration.

        Args:
            camera_config: CameraConfig object containing the camera configuration

        Returns:
            tuple: (camera_instance, error, message)
        """
        if not isinstance(camera_config, CameraConfig):
            return None, "Config must be a CameraConfig instance", "Invalid config type"

        # Create camera instance
        camera_instance = Camera(self.session, camera_config)

        # Save to backend
        result, error, message = camera_instance.save(account_number=self.account_number)

        if error:
            return result, error, message

        return camera_instance, None, message

    def get_camera_by_id(
        self, camera_id: str
    ) -> Tuple[Optional["Camera"], Optional[str], str]:
        """
        Get a camera by its ID.

        Args:
            camera_id: The ID of the camera to retrieve

        Returns:
            tuple: (camera_instance, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"

        try:
            camera_instance = Camera(self.session, camera_id=camera_id)
            return camera_instance, None, "Camera retrieved successfully"
        except Exception as e:
            return None, str(e), "Failed to retrieve camera"

    def list_camera_configs(
        self, page: int = 1, limit: int = 10, search: str = None, group_id: str = None
    ) -> Tuple[Optional[List[Dict]], Optional[str], str]:
        """
        List all camera configs for account (updated to use account-based approach).

        Returns:
            tuple: (camera_configs, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"

        # Use account-based camera stream endpoint
        if group_id:
            # Get cameras for specific group using new API
            return self.get_cameras(group_id=group_id, limit=limit)
        else:
            # Get all cameras for account using paginated endpoint
            path = f"/v1/inference/all_camera_streams_pag/{self.account_number}"
            params = {"page": page, "limit": limit}
            if search:
                params["search"] = search

        resp = self.rpc.get(path=path, params=params)

        result, error, message = self.handle_response(
            resp, "Cameras retrieved successfully", "Failed to retrieve cameras"
        )

        if error:
            return None, error, message

        if result and "items" in result:
            cameras_list = result["items"]
            logging.debug(
                "list_camera_configs: account_number=%s page=%s limit=%s group_id=%s -> cameras=%s",
                self.account_number,
                page,
                limit,
                group_id,
                len(cameras_list),
            )
            return cameras_list, None, message

        return [], None, message

    def get_cameras(
        self, page: int = 1, limit: int = 10, search: str = None, group_id: str = None
    ) -> Tuple[Optional[List["Camera"]], Optional[str], str]:
        """
        Get all cameras for a specific deployment.

        Args:
            page: Page number for pagination
            limit: Items per page
            search: Optional search term
            group_id: Optional filter by camera group ID

        Returns:
            tuple: (camera_instances, error, message)
        """
        logging.debug(
            "get_cameras: account_number=%s page=%s limit=%s group_id=%s search=%s",
            self.account_number,
            page,
            limit,
            group_id,
            search,
        )
        cameras, error, message = self.list_camera_configs(
            page=page, limit=limit, search=search, group_id=group_id
        )
        if error:
            return None, error, message

        camera_instances = []
        for config_data in cameras:
            try:
                camera_config = CameraConfig.from_dict(config_data)
                if group_id and camera_config.camera_group_id != group_id:
                    continue
                camera_instance = Camera(self.session, camera_config)
                camera_instances.append(camera_instance)
            except Exception as e:
                logging.warning(f"Failed to parse camera config data: {e}")
                continue

        logging.debug(
            "get_cameras: built_instances=%s (after parsing/filtering)",
            len(camera_instances),
        )
        return camera_instances, None, message

    def get_stream_url(
        self, config_id: str
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        Get the stream URL for a camera configuration.

        Args:
            config_id: The ID of the camera configuration

        Returns:
            tuple: (stream_url, error, message)
        """
        if not config_id:
            return None, "Config ID is required", "Invalid config ID"

        path = f"/v1/inference/get_simulated_stream_url/{config_id}"
        resp = self.rpc.get(path=path)
        result, error, message = self.handle_response(
            resp, "Stream URL retrieved successfully", "Failed to retrieve stream URL"
        )
        return result, error, message

    def update_camera(
        self, camera_id: str, camera_config: CameraConfig
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update an existing camera configuration.

        Args:
            camera_id: The ID of the camera to update
            camera_config: CameraConfig object with updated configuration

        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"

        if not isinstance(camera_config, CameraConfig):
            return None, "Config must be a CameraConfig instance", "Invalid config type"

        path = f"/v1/inference/update_camera_stream/{camera_id}"
        payload = camera_config.to_dict()

        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp, "Camera updated successfully", "Failed to update camera"
        )

    def delete_camera(
        self, camera_id: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete a camera by its ID.

        Args:
            camera_id: The ID of the camera to delete

        Returns:
            tuple: (result, error, message)
        """
        if not camera_id:
            return None, "Camera ID is required", "Invalid camera ID"

        path = f"/v1/inference/delete_camera_stream/{camera_id}"
        resp = self.rpc.delete(path=path)

        return self.handle_response(
            resp, "Camera deleted successfully", "Failed to delete camera"
        )

    def delete_all_cameras(
        self, confirm: bool = False
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete all cameras for account using individual camera deletion.

        Args:
            confirm: Must be True to confirm bulk deletion

        Returns:
            tuple: (result, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"

        if not confirm:
            return (
                None,
                "Must confirm bulk deletion by setting confirm=True",
                "Confirmation required",
            )

        # Get all cameras for the account first
        cameras, error, message = self.get_cameras(limit=1000)  # Get up to 1000 cameras
        if error:
            return None, f"Failed to retrieve cameras for deletion: {error}", message

        if not cameras:
            return {"deleted_count": 0}, None, "No cameras found to delete"

        # Delete cameras individually
        deleted_count = 0
        failed_deletions = []
        
        for camera in cameras:
            try:
                if hasattr(camera, 'delete'):
                    result, del_error, del_message = camera.delete()
                    if del_error:
                        failed_deletions.append(f"Camera {getattr(camera, 'id', 'unknown')}: {del_error}")
                    else:
                        deleted_count += 1
                else:
                    # Fallback to direct deletion if Camera object doesn't have delete method
                    camera_id = getattr(camera, 'id', None)
                    if camera_id:
                        result, del_error, del_message = self.delete_camera_by_id(camera_id)
                        if del_error:
                            failed_deletions.append(f"Camera {camera_id}: {del_error}")
                        else:
                            deleted_count += 1
            except Exception as e:
                camera_id = getattr(camera, 'id', 'unknown')
                failed_deletions.append(f"Camera {camera_id}: {str(e)}")

        result = {"deleted_count": deleted_count, "total_found": len(cameras)}
        
        if failed_deletions:
            error_msg = f"Partial deletion completed. Failures: {'; '.join(failed_deletions[:5])}"  # Limit to first 5 errors
            if len(failed_deletions) > 5:
                error_msg += f"... and {len(failed_deletions) - 5} more"
            return result, error_msg, f"Deleted {deleted_count}/{len(cameras)} cameras"
        
        return result, None, f"Successfully deleted all {deleted_count} cameras"

    # Bulk Operations

    def add_cameras_to_group(
        self, group_id: str, camera_configs: List[CameraConfig]
    ) -> Tuple[Optional[List["Camera"]], Optional[str], str]:
        """
        Add multiple cameras to a camera group using individual camera creation.

        Args:
            group_id: The ID of the camera group
            camera_configs: List of CameraConfig objects

        Returns:
            tuple: (camera_instances, error, message)
        """
        if not group_id:
            return None, "Group ID is required", "Invalid group ID"

        if not camera_configs:
            return None, "Camera configs are required", "Invalid configs"

        if not all(isinstance(config, CameraConfig) for config in camera_configs):
            return (
                None,
                "All configs must be CameraConfig instances",
                "Invalid config types",
            )

        # Set camera group ID and account number for all configs
        for config in camera_configs:
            config.camera_group_id = group_id
            config.account_number = self.account_number

        # Create cameras individually using new API
        created_cameras = []
        failed_cameras = []
        
        for i, config in enumerate(camera_configs):
            try:
                camera_instance = self.create_camera(config)
                if isinstance(camera_instance, tuple):
                    camera, error, message = camera_instance
                    if error:
                        failed_cameras.append(f"Camera {i+1}: {error}")
                        continue
                    created_cameras.append(camera)
                else:
                    created_cameras.append(camera_instance)
            except Exception as e:
                failed_cameras.append(f"Camera {i+1}: {str(e)}")

        if failed_cameras:
            error_msg = "; ".join(failed_cameras)
            if not created_cameras:
                return None, error_msg, "Failed to create any cameras"
            else:
                # Partial success
                return created_cameras, error_msg, f"Created {len(created_cameras)} cameras with some failures"
        
        return created_cameras, None, f"Successfully created {len(created_cameras)} cameras"

    def _validate_camera_group(self, group: CameraGroupConfig) -> Tuple[bool, str]:
        """
        Validate camera group data before API calls.

        Args:
            group: CameraGroup object to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not group.camera_group_name or not group.camera_group_name.strip():
            return False, "Camera group name is required"

        if not group.streaming_gateway_id:
            return False, "Streaming gateway ID is required"
        
        if not group.default_stream_settings:
            return False, "Default stream settings are required"

        # Validate stream settings
        settings = group.default_stream_settings
        if settings.aspect_ratio not in ["16:9", "4:3", "1:1"]:
            return False, "Aspect ratio must be one of: 16:9, 4:3, 1:1"

        if not (0 <= settings.video_quality <= 100):
            return False, "Video quality must be between 0 and 100"

        if settings.height <= 0:
            return False, "Height must be greater than 0"

        if settings.width <= 0:
            return False, "Width must be greater than 0"

        if settings.fps <= 0:
            return False, "FPS must be greater than 0"
        
        if settings.streaming_fps and settings.streaming_fps <= 0:
            return False, "Streaming FPS must be greater than 0"

        return True, ""

    def _validate_camera_config(self, config: CameraConfig) -> Tuple[bool, str]:
        """
        Validate camera configuration data before API calls.

        Args:
            config: CameraConfig object to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        if not config.camera_name or not config.camera_name.strip():
            return False, "Camera name is required"

        if not config.stream_url or not config.stream_url.strip():
            return False, "Stream URL is required"

        if not config.camera_group_id:
            return False, "Camera group ID is required"

        # Validate custom stream settings if provided
        if config.custom_stream_settings:
            custom = config.custom_stream_settings

            if "aspectRatio" in custom and custom["aspectRatio"] not in [
                "16:9",
                "4:3",
                "1:1",
            ]:
                return False, "Custom aspect ratio must be one of: 16:9, 4:3, 1:1"

            if "videoQuality" in custom and not (0 <= custom["videoQuality"] <= 100):
                return False, "Custom video quality must be between 0 and 100"

            if "height" in custom and custom["height"] <= 0:
                return False, "Custom height must be greater than 0"

            if "width" in custom and custom["width"] <= 0:
                return False, "Custom width must be greater than 0"

            if "fps" in custom and custom["fps"] <= 0:
                return False, "Custom FPS must be greater than 0"

        return True, ""

    # Legacy method aliases for backward compatibility
    def add_camera_config(
        self, config: CameraConfig
    ) -> Tuple[Optional["Camera"], Optional[str], str]:
        """Legacy method - use create_camera instead."""
        return self.create_camera(config)

    def get_camera_config_by_id(
        self, config_id: str
    ) -> Tuple[Optional["Camera"], Optional[str], str]:
        """Legacy method - use get_camera_by_id instead."""
        return self.get_camera_by_id(config_id)

    def get_camera_configs(
        self, page: int = 1, limit: int = 10, search: str = None, group_id: str = None
    ) -> Tuple[Optional[List["Camera"]], Optional[str], str]:
        """Legacy method - use get_cameras instead."""
        return self.get_cameras(page, limit, search, group_id)

    def update_camera_config(
        self, config_id: str, config: CameraConfig
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """Legacy method - use update_camera instead."""
        return self.update_camera(config_id, config)

    def delete_camera_config_by_id(
        self, config_id: str
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """Legacy method - use delete_camera instead."""
        return self.delete_camera(config_id)

    def delete_camera_configs(
        self, confirm: bool = False
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """Legacy method - use delete_all_cameras instead."""
        return self.delete_all_cameras(confirm)

    def add_camera_configs(
        self, configs: List[CameraConfig]
    ) -> Tuple[Optional[Dict], Optional[str], str]:
        """Legacy method - use add_cameras_to_group instead."""
        if not configs:
            return None, "Camera configs are required", "Invalid configs"

        # Use the first config's group ID
        group_id = configs[0].camera_group_id if configs else None
        if not group_id:
            return None, "Camera group ID is required", "Invalid group ID"

        cameras, error, message = self.add_cameras_to_group(group_id, configs)
        if error:
            return None, error, message

        return {"cameras": [cam.config.to_dict() for cam in cameras]}, None, message
