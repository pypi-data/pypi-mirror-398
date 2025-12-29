"""Frame processing utilities."""
import cv2
import numpy as np
from typing import Tuple, Optional


class FrameProcessor:
    """Handles frame processing operations like resizing."""
    
    @staticmethod
    def resize_frame(
        frame: np.ndarray,
        target_width: Optional[int],
        target_height: Optional[int]
    ) -> np.ndarray:
        """Resize frame if needed.
        
        Args:
            frame: Input frame
            target_width: Target width (None to keep current)
            target_height: Target height (None to keep current)
            
        Returns:
            Resized frame or original if no resize needed
        """
        if not target_width and not target_height:
            return frame
        
        current_h, current_w = frame.shape[:2]
        final_w = target_width if target_width else current_w
        final_h = target_height if target_height else current_h
        
        if final_w != current_w or final_h != current_h:
            return cv2.resize(frame, (final_w, final_h))
        
        return frame
    
    @staticmethod
    def should_skip_frame(frame_counter: int, frame_skip: int) -> bool:
        """Check if frame should be skipped based on skip rate.
        
        Args:
            frame_counter: Current frame count
            frame_skip: Frame skip rate
            
        Returns:
            True if frame should be skipped
        """
        return frame_counter % frame_skip != 0
    
    @staticmethod
    def calculate_actual_dimensions(
        video_width: int,
        video_height: int,
        target_width: Optional[int],
        target_height: Optional[int]
    ) -> Tuple[int, int]:
        """Calculate actual output dimensions.
        
        Args:
            video_width: Original video width
            video_height: Original video height
            target_width: Target width (None for original)
            target_height: Target height (None for original)
            
        Returns:
            Tuple of (actual_width, actual_height)
        """
        actual_width = target_width if target_width else video_width
        actual_height = target_height if target_height else video_height
        return actual_width, actual_height

