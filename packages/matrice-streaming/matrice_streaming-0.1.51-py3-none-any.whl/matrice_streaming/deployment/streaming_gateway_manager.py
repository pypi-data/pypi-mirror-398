"""Module providing streaming gateway manager functionality for deployments."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class NetworkSettings:
    """
    Network settings data class for streaming gateway configurations.
    
    Attributes:
        ip_address: IP address of the gateway
        port: Port number for the gateway
        access_scale: Access scale (local|regional|global)
        region: Region identifier (e.g., us-east-1)
        max_bandwidth_mbps: Maximum bandwidth in Mbps
        current_bandwidth_mbps: Current bandwidth usage in Mbps
    """
    ip_address: str
    port: int
    access_scale: str
    region: str
    max_bandwidth_mbps: Optional[float] = None
    current_bandwidth_mbps: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert network settings to dictionary for API calls."""
        data = {
            "IPAddress": self.ip_address,
            "port": self.port,
            "accessScale": self.access_scale,
            "region": self.region
        }
        if self.max_bandwidth_mbps is not None:
            data["maxBandwidthMbps"] = self.max_bandwidth_mbps
        if self.current_bandwidth_mbps is not None:
            data["currentBandwidthMbps"] = self.current_bandwidth_mbps
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NetworkSettings":
        """Create NetworkSettings instance from API response data."""
        return cls(
            ip_address=data.get("IPAddress", ""),
            port=data.get("port", 0),
            access_scale=data.get("accessScale", ""),
            region=data.get("region", ""),
            max_bandwidth_mbps=data.get("maxBandwidthMbps"),
            current_bandwidth_mbps=data.get("currentBandwidthMbps")
        )


@dataclass
class StreamingGatewayConfig:
    """
    Streaming gateway configuration data class.
    
    Attributes:
        gateway_name: Name of the streaming gateway
        description: Description of the streaming gateway
        status: Status of the streaming gateway (active, inactive, starting, stopped)
        network_settings: Network configuration settings
        account_number: Account number for the gateway
        action_record_id: Action record ID for tracking
        start_time: Start time timestamp
        last_stream_time: Last streaming time timestamp
        id: Unique identifier for the streaming gateway (MongoDB ObjectID)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    gateway_name: str
    description: str
    status: str
    network_settings: NetworkSettings
    account_number: Optional[str] = None
    action_record_id: Optional[str] = None
    start_time: Optional[str] = None
    last_stream_time: Optional[str] = None
    id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert the streaming gateway config to a dictionary for API calls."""
        if not self.gateway_name or not self.gateway_name.strip():
            raise ValueError("Gateway name is required")
        if not self.description or not self.description.strip():
            raise ValueError("Gateway description is required")
        if not self.status:
            raise ValueError("Gateway status is required")
        if not self.network_settings:
            raise ValueError("Network settings are required")
            
        data = {
            "gatewayName": self.gateway_name,
            "description": self.description,
            "status": self.status,
            "networkSettings": self.network_settings.to_dict()
        }
        
        if self.account_number:
            data["accountNumber"] = self.account_number
        if self.action_record_id:
            data["actionRecordID"] = self.action_record_id
        if self.start_time:
            data["startTime"] = self.start_time
        if self.last_stream_time:
            data["lastStreamTime"] = self.last_stream_time
        if self.id:
            data["_id"] = self.id
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StreamingGatewayConfig':
        """Create a StreamingGatewayConfig instance from API response data."""
        network_settings_data = data.get("networkSettings", {})
        network_settings = NetworkSettings.from_dict(network_settings_data) if network_settings_data else None
        
        return cls(
            id=data.get("_id") or data.get("id") or data.get("ID"),
            gateway_name=data.get("gatewayName") or data.get("name") or data.get("Name") or "",
            description=data.get("description") or data.get("Description") or "",
            status=data.get("status") or data.get("Status") or "inactive",
            network_settings=network_settings,
            account_number=data.get("accountNumber"),
            action_record_id=data.get("actionRecordID"),
            start_time=data.get("startTime"),
            last_stream_time=data.get("lastStreamTime"),
            created_at=data.get("createdAt") or data.get("CreatedAt"),
            updated_at=data.get("updatedAt") or data.get("UpdatedAt")
        )


class StreamingGateway:
    """
    Streaming gateway instance class for managing individual streaming gateways.
    
    This class represents a single streaming gateway and provides methods to manage
    its configuration, camera groups, and operational status.
    
    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.streaming_gateway_manager import StreamingGateway, StreamingGatewayConfig
        
        session = Session(account_number="...", access_key="...", secret_key="...")
        
        # Create network settings
        network_settings = NetworkSettings(
            ip_address="10.0.0.5",
            port=9092,
            access_scale="regional",
            region="us-east-1",
            max_bandwidth_mbps=150.5,
            current_bandwidth_mbps=120.3
        )
        
        # Create gateway config
        config = StreamingGatewayConfig(
            gateway_name="Main Gateway",
            description="Primary streaming gateway",
            status="active",
            network_settings=network_settings,
            account_number="ACC-123"
        )
        
        # Create gateway instance
        gateway = StreamingGateway(session, config)
        
        # Save to backend
        result, error, message = gateway.save()
        if not error:
            print(f"Gateway created with ID: {gateway.id}")
            
        # Update configuration
        gateway.description = "Updated description"
        result, error, message = gateway.update()
        
        # Start streaming
        result, error, message = gateway.start_streaming()
        
        # Update status
        result, error, message = gateway.update_status("active")
        
        # Stop streaming
        result, error, message = gateway.stop_streaming()
        ```
    """
    
    def __init__(self, session, config: StreamingGatewayConfig = None, gateway_id: str = None):
        """
        Initialize a StreamingGateway instance.
        
        Args:
            session: Session object containing RPC client for API communication
            config: StreamingGatewayConfig object (for new gateways)
            gateway_id: ID of existing gateway to load (mutually exclusive with config)
        """
        if not config and not gateway_id:
            raise ValueError("Either config or gateway_id must be provided")
        
        self.session = session
        self.rpc = session.rpc
        
        if gateway_id:
            # Load existing gateway
            self.config = None
            self._load_from_id(gateway_id)
        else:
            # New gateway from config
            self.config = config
    
    @property
    def id(self) -> Optional[str]:
        """Get the gateway ID."""
        return self.config.id if self.config else None
    
    @property
    def gateway_name(self) -> str:
        """Get the gateway name."""
        return self.config.gateway_name if self.config else ""
    
    @gateway_name.setter
    def gateway_name(self, value: str):
        """Set the gateway name."""
        if self.config:
            self.config.gateway_name = value
    
    @property
    def name(self) -> str:
        """Get the gateway name (alias for gateway_name)."""
        return self.gateway_name
    
    @name.setter
    def name(self, value: str):
        """Set the gateway name (alias for gateway_name)."""
        self.gateway_name = value
    
    @property
    def description(self) -> Optional[str]:
        """Get the gateway description."""
        return self.config.description if self.config else None
    
    @description.setter
    def description(self, value: str):
        """Set the gateway description."""
        if self.config:
            self.config.description = value
    
    @property
    def network_settings(self) -> Optional[NetworkSettings]:
        """Get the network settings."""
        return self.config.network_settings if self.config else None
    
    @network_settings.setter
    def network_settings(self, value: NetworkSettings):
        """Set the network settings."""
        if self.config:
            self.config.network_settings = value
    
    @property
    def status(self) -> Optional[str]:
        """Get the gateway status."""
        return self.config.status if self.config else None
    
    @property
    def account_number(self) -> Optional[str]:
        """Get the account number."""
        return self.config.account_number if self.config else None
    
    @account_number.setter
    def account_number(self, value: str):
        """Set the account number."""
        if self.config:
            self.config.account_number = value
    
    def _load_from_id(self, gateway_id: str):
        """Load gateway configuration from backend by ID."""
        path = f"/v1/inference/get_streaming_gateways/{gateway_id}"
        resp = self.rpc.get(path=path)
        
        if resp and resp.get("success"):
            data = resp.get("data")
            if data:
                self.config = StreamingGatewayConfig.from_dict(data)
            else:
                raise ValueError(f"No data found for gateway ID: {gateway_id}")
        else:
            error_msg = resp.get("message") if resp else "No response received"
            raise ValueError(f"Failed to load gateway: {error_msg}")
    
    def save(self, account_number: str = None) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Save the gateway configuration to the backend (create new).
        
        Args:
            account_number: The account number to associate with the gateway
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config:
            return None, "No configuration to save", "Invalid state"
        
        if self.id:
            return None, "Gateway already exists, use update() instead", "Already exists"
        
        if account_number:
            self.config.account_number = account_number
        
        if not self.config.account_number:
            return None, "Account number is required", "Missing account number"
        
        path = "/v1/inference/create_streaming_gateway"
        payload = self.config.to_dict()
        
        resp = self.rpc.post(path=path, payload=payload)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            if result and "id" in result:
                self.config.id = result["id"]
            return result, None, "Streaming gateway created successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to create streaming gateway"
    
    def update(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update the gateway configuration in the backend.
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Gateway must be saved before updating", "Invalid state"
        
        path = f"/v1/inference/update_streaming_gateway/{self.config.id}"
        payload = {
            "gatewayName": self.config.gateway_name,
            "description": self.config.description,
            "status": self.config.status
        }
        
        if self.config.network_settings:
            payload["networkSettings"] = self.config.network_settings.to_dict()
        
        resp = self.rpc.put(path=path, payload=payload)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Streaming gateway updated successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to update streaming gateway"
    
    def delete(self, force: bool = False) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Delete the gateway from the backend.
        
        Args:
            force: Force delete even if active
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Gateway must be saved before deleting", "Invalid state"
        
        path = f"/v1/inference/delete_streaming_gateway/{self.config.id}"
        params = {}
        if force:
            params["force"] = "true"
        
        resp = self.rpc.delete(path=path, params=params)
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Streaming gateway deleted successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to delete streaming gateway"
    
    def start_streaming(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Start the streaming gateway.
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Gateway must be saved before starting", "Invalid state"
        
        path = f"/v1/inference/start_streaming_gateway/{self.config.id}"
        
        resp = self.rpc.post(path=path, payload={})
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Streaming gateway started successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to start streaming gateway"
    
    def stop_streaming(self) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Stop the streaming gateway.
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Gateway must be saved before stopping", "Invalid state"
        
        path = f"/v1/inference/stop_streaming_gateway/{self.config.id}"
        
        resp = self.rpc.post(path=path, payload={})
        
        if resp and resp.get("success"):
            result = resp.get("data")
            return result, None, "Streaming gateway stopped successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to stop streaming gateway"
    
    def update_status(self, status: str) -> Tuple[Optional[Dict], Optional[str], str]:
        """
        Update the status of the streaming gateway.
        
        Args:
            status: New status (active, inactive, starting, stopped, etc.)
        
        Returns:
            tuple: (result, error, message)
        """
        if not self.config or not self.config.id:
            return None, "Gateway must be saved before updating status", "Invalid state"
        
        if not status:
            return None, "Status is required", "Invalid status"
        
        path = f"/v1/inference/update_streaming_gateway_status/{self.config.id}"
        payload = {"status": status}
        
        resp = self.rpc.put(path=path, payload=payload)
        
        if resp and resp.get("success"):
            # Update local configuration
            self.config.status = status
            result = resp.get("data")
            return result, None, "Streaming gateway status updated successfully"
        else:
            error = resp.get("message") if resp else "No response received"
            return None, error, "Failed to update streaming gateway status"
    
    def refresh(self):
        """Refresh the gateway configuration from the backend."""
        if self.config and self.config.id:
            self._load_from_id(self.config.id)


class StreamingGatewayManager:
    """
    Streaming gateway manager client for handling streaming gateway configurations in deployments.
    
    This class provides methods to create, read, update, and delete streaming gateway configurations
    that manage collections of camera groups for efficient video processing and distribution.
    
    Example:
        Basic usage:
        ```python
        from matrice import Session
        from matrice_streaming.deployment.streaming_gateway_manager import StreamingGatewayManager, StreamingGatewayConfig
        
        session = Session(account_number="...", access_key="...", secret_key="...")
        gateway_manager = StreamingGatewayManager(session)
        
        # Create network settings
        network_settings = NetworkSettings(
            ip_address="10.0.0.5",
            port=9092,
            access_scale="regional",
            region="us-east-1"
        )
        
        # Create a streaming gateway config
        config = StreamingGatewayConfig(
            gateway_name="Main Streaming Gateway",
            description="Primary gateway for building A camera groups",
            status="active",
            network_settings=network_settings
        )
        
        # Create gateway through manager
        gateway, error, message = gateway_manager.create_streaming_gateway(config)
        if error:
            print(f"Error: {error}")
        else:
            print(f"Streaming gateway created: {gateway.name}")
            
        # Get all gateways for the account
        gateways, error, message = gateway_manager.get_streaming_gateways()
        if not error:
            for gateway in gateways:
                print(f"Gateway: {gateway.name} - Status: {gateway.status}")
        ```
    """
    
    def __init__(self, session, account_number: str = None):
        """
        Initialize the StreamingGatewayManager client.
        
        Args:
            session: Session object containing RPC client for API communication
            account_number: The account number for API calls
        """
        self.session = session
        self.rpc = session.rpc
        self.account_number = account_number or getattr(session, 'account_number', None)

    def handle_response(self, response: Dict, success_message: str, failure_message: str) -> Tuple[Optional[Dict], Optional[str], str]:
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

    def create_streaming_gateway(self, config: StreamingGatewayConfig) -> Tuple[Optional['StreamingGateway'], Optional[str], str]:
        """
        Create a new streaming gateway from configuration.
        
        Args:
            config: StreamingGatewayConfig object containing the gateway configuration
            
        Returns:
            tuple: (streaming_gateway, error, message)
                - streaming_gateway: StreamingGateway instance if successful, None otherwise
                - error: Error message if failed, None otherwise  
                - message: Status message
        """
        if not isinstance(config, StreamingGatewayConfig):
            return None, "Config must be a StreamingGatewayConfig instance", "Invalid config type"
        
        # Validate gateway config
        is_valid, validation_error = self._validate_streaming_gateway_config(config)
        if not is_valid:
            return None, validation_error, "Validation failed"
        
        # Create gateway instance
        gateway = StreamingGateway(self.session, config)
        
        # Save to backend
        result, error, message = gateway.save(account_number=self.account_number)
        
        if error:
            return None, error, message
        
        return gateway, None, message
    
    def get_streaming_gateway_by_id(self, gateway_id: str) -> Tuple[StreamingGateway, Optional[str], str]:
        """
        Get a streaming gateway by its ID.
        
        Args:
            gateway_id: The ID of the streaming gateway to retrieve
            
        Returns:
            tuple: (streaming_gateway, error, message)
        """
        if not gateway_id:
            return None, "Gateway ID is required", "Invalid gateway ID"
        
        try:
            gateway = StreamingGateway(self.session, gateway_id=gateway_id)
            return gateway, None, "Streaming gateway retrieved successfully"
        except Exception as e:
            return None, str(e), "Failed to retrieve streaming gateway"
    
    def get_streaming_gateways(self, page: int = 1, limit: int = 10) -> Tuple[Optional[List['StreamingGateway']], Optional[str], str]:
        """
        Get all streaming gateways for the account.
        
        Args:
            page: Page number for pagination
            limit: Items per page
            
        Returns:
            tuple: (streaming_gateways, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"
        
        path = f"/v1/inference/streaming_gateways_by_acc_number/{self.account_number}"
        params = {"page": page, "limit": limit} if page > 1 or limit != 10 else {}
            
        resp = self.rpc.get(path=path, params=params)
        
        result, error, message = self.handle_response(
            resp,
            "Streaming gateways retrieved successfully",
            "Failed to retrieve streaming gateways"
        )
        
        if error:
            return None, error, message
        
        if result:
            try:
                # Handle different response structures
                if isinstance(result, dict) and "data" in result:
                    gateway_data_list = result["data"]
                elif isinstance(result, dict) and "items" in result:
                    gateway_data_list = result["items"]
                elif isinstance(result, list):
                    gateway_data_list = result
                else:
                    gateway_data_list = []
                
                if not gateway_data_list:
                    logging.debug(
                        "get_streaming_gateways: account_number=%s page=%s limit=%s -> 0 gateways",
                        self.account_number,
                        page,
                        limit,
                    )
                    return [], None, "No streaming gateways found"
                
                # Convert to StreamingGateway instances
                streaming_gateways = []
                for gateway_data in gateway_data_list:
                    try:
                        config = StreamingGatewayConfig.from_dict(gateway_data)
                        gateway = StreamingGateway(self.session, config)
                        streaming_gateways.append(gateway)
                    except Exception as e:
                        logging.warning(f"Failed to parse gateway data: {e}")
                        continue
                
                logging.debug(
                    "get_streaming_gateways: account_number=%s -> gateways=%s",
                    self.account_number,
                    len(streaming_gateways),
                )
                return streaming_gateways, None, message
            except Exception as e:
                return None, f"Failed to parse streaming gateways: {str(e)}", "Parse error"
        
        return [], None, message
    
    def get_streaming_gateways_paginated(self, page: int = 1, limit: int = 10) -> Tuple[Optional[List['StreamingGateway']], Optional[str], str]:
        """
        Get paginated streaming gateways for the account.
        
        Args:
            page: Page number for pagination
            limit: Items per page
            
        Returns:
            tuple: (streaming_gateways, error, message)
        """
        if not self.account_number:
            return None, "Account number is required", "Invalid account number"
        
        path = f"/v1/inference/all_streaming_gateways_pag/{self.account_number}"
        params = {"page": page, "limit": limit}
            
        resp = self.rpc.get(path=path, params=params)
        
        result, error, message = self.handle_response(
            resp,
            "Streaming gateways retrieved successfully",
            "Failed to retrieve streaming gateways"
        )
        
        if error:
            return None, error, message
        
        if result:
            try:
                # Handle paginated response structure
                if isinstance(result, dict):
                    gateway_data_list = result.get("items", result.get("data", []))
                elif isinstance(result, list):
                    gateway_data_list = result
                else:
                    gateway_data_list = []
                
                # Convert to StreamingGateway instances
                streaming_gateways = []
                for gateway_data in gateway_data_list:
                    try:
                        config = StreamingGatewayConfig.from_dict(gateway_data)
                        gateway = StreamingGateway(self.session, config)
                        streaming_gateways.append(gateway)
                    except Exception as e:
                        logging.warning(f"Failed to parse gateway data: {e}")
                        continue
                
                return streaming_gateways, None, message
            except Exception as e:
                return None, f"Failed to parse streaming gateways: {str(e)}", "Parse error"
        
        return [], None, message

    def _validate_streaming_gateway_config(self, config: StreamingGatewayConfig) -> Tuple[bool, str]:
        """
        Validate streaming gateway config data before API calls.
        
        Args:
            config: StreamingGatewayConfig object to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not config.gateway_name or not config.gateway_name.strip():
            return False, "Streaming gateway name is required"
        
        if not config.description or not config.description.strip():
            return False, "Streaming gateway description is required"
        
        if not config.status:
            return False, "Streaming gateway status is required"
        
        if not config.network_settings:
            return False, "Network settings are required"
        
        # Validate network settings
        if not config.network_settings.ip_address:
            return False, "IP address is required in network settings"
        
        if not config.network_settings.port or config.network_settings.port <= 0:
            return False, "Valid port is required in network settings"
        
        if not config.network_settings.access_scale:
            return False, "Access scale is required in network settings"
        
        if config.network_settings.access_scale not in ["local", "regional", "global"]:
            return False, "Access scale must be 'local', 'regional', or 'global'"
        
        if not config.network_settings.region:
            return False, "Region is required in network settings"
        
        return True, "" 