"""
Debug UI module for AeroControl.
Displays real-time visualization of hand tracking and gestures.
"""

import cv2
import logging
import numpy as np
from typing import Optional


logger = logging.getLogger(__name__)


class DebugUI:
    """
    Debug overlay window showing tracking status.
    """
    
    def __init__(self, window_name: str = "AeroControl Debug"):
        """
        Initialize debug UI.
        
        Args:
            window_name: Name of the OpenCV window
        """
        self.window_name = window_name
        self.enabled = False
    
    def enable(self):
        """Enable debug UI."""
        self.enabled = True
        cv2.namedWindow(self.window_name)
        logger.info("Debug UI enabled")
    
    def disable(self):
        """Disable debug UI."""
        if self.enabled:
            cv2.destroyWindow(self.window_name)
            self.enabled = False
            logger.info("Debug UI disabled")
    
    def draw(self, frame: np.ndarray, info: dict):
        """
        Draw debug information on frame.
        
        Args:
            frame: Camera frame
            info: Dictionary with debug information
        """
        if not self.enabled:
            return
        
        display_frame = frame.copy()
        h, w = display_frame.shape[:2]
        
        # Draw info panel background
        cv2.rectangle(display_frame, (10, 10), (w - 10, 200), (0, 0, 0), -1)
        cv2.rectangle(display_frame, (10, 10), (w - 10, 200), (0, 255, 0), 2)
        
        # Draw text information
        y_offset = 40
        line_height = 30
        
        texts = [
            f"FPS: {info.get('fps', 0):.1f}",
            f"Gesture: {info.get('gesture', 'None')}",
            f"Smoothing: {info.get('alpha', 0):.3f}",
            f"Hand Scale: {info.get('hand_scale', 0):.1f}",
            f"Cursor: ({info.get('cursor_x', 0)}, {info.get('cursor_y', 0)})",
        ]
        
        for i, text in enumerate(texts):
            cv2.putText(display_frame, text, (20, y_offset + i * line_height),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw cursor position indicator
        cursor_x = info.get('cursor_cam_x')
        cursor_y = info.get('cursor_cam_y')
        if cursor_x is not None and cursor_y is not None:
            cv2.circle(display_frame, (int(cursor_x), int(cursor_y)), 
                      15, (0, 0, 255), 3)
            cv2.circle(display_frame, (int(cursor_x), int(cursor_y)), 
                      5, (0, 0, 255), -1)
        
        # Show frame
        cv2.imshow(self.window_name, display_frame)
        cv2.waitKey(1)