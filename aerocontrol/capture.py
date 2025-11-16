import cv2
import logging
import time
from typing import Optional, Tuple
import numpy as np


logger = logging.getLogger(__name__)


class CameraCapture:
    """
    Manages camera capture with performance monitoring.
    """
    
    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        """
        Initialize camera capture.
        
        Args:
            camera_id: Camera device index
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Target frames per second
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.target_fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
    def open(self) -> bool:
        """
        Open the camera device.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Verify actual settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            logger.info(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            return True
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera.
        
        Returns:
            Tuple of (success, frame)
        """
        if self.cap is None or not self.cap.isOpened():
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            self._update_fps()
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
        
        return ret, frame
    
    def _update_fps(self):
        """Update FPS counter."""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self.current_fps
    
    def close(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("Camera closed")