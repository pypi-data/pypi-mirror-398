"""Kafka event listener for camera events using generic EventListener."""
import logging
from typing import Any, Dict
from matrice_common.session import Session
from matrice_common.stream import EventListener as GenericEventListener
from .dynamic_camera_manager import DynamicCameraManager


class EventListener:
    """Listener for camera add/update/delete events from Kafka.

    This class wraps the generic EventListener from matrice_common
    and provides camera-specific event handling logic.
    """

    def __init__(
        self,
        session: Session,
        streaming_gateway_id: str,
        camera_manager: DynamicCameraManager,
    ) -> None:
        """Initialize event listener.

        Args:
            session: Session object for authentication
            streaming_gateway_id: ID of streaming gateway to filter events
            camera_manager: Camera manager instance
        """
        self.streaming_gateway_id = streaming_gateway_id
        self.camera_manager = camera_manager
        self.session = session
        self.logger = logging.getLogger(__name__)

        # Create generic event listener for Camera_Events_Topic
        self._listener = GenericEventListener(
            session=session,
            topics=['Camera_Events_Topic'],
            event_handler=self.handle_event,
            filter_field='streamingGatewayId',
            filter_value=streaming_gateway_id,
            consumer_group_id=f"stg_camera_events_{streaming_gateway_id}"
        )

        self.logger.info(f"Camera EventListener initialized for gateway {streaming_gateway_id}")

    @property
    def is_listening(self) -> bool:
        """Check if listener is active."""
        return self._listener.is_listening

    def start(self) -> bool:
        """Start listening to camera events.

        Returns:
            bool: True if started successfully
        """
        return self._listener.start()

    def stop(self):
        """Stop listening."""
        self._listener.stop()
    
    def handle_event(self, event: Dict[str, Any]):
        """Handle camera event.

        Args:
            event: Camera event dict
        """
        event_type = event.get('eventType')
        camera_data = event.get('data', {})
        camera_id = camera_data.get('id')
        camera_name = camera_data.get('cameraName', 'Unknown')

        self.logger.info(f"Handling {event_type} event for camera: {camera_name}")

        try:
            if event_type == 'add':
                self.camera_manager.add_camera(camera_data)
            elif event_type == 'update':
                self.camera_manager.update_camera(camera_data)
            elif event_type == 'delete':
                self.camera_manager.remove_camera(camera_id)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")

        except Exception as e:
            self.logger.error(f"Error handling {event_type} for {camera_id}: {e}")

    def get_statistics(self) -> dict:
        """Get statistics."""
        return self._listener.get_statistics()
        

