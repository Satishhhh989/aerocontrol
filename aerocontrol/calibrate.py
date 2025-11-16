"""
Calibration module for AeroControl.
Provides screen coordinate mapping and sensitivity calibration.
"""

import cv2
import logging
import numpy as np
from typing import Tuple, List


logger = logging.getLogger(__name__)


class Calibrator:
    """
    Handles calibration of camera-to-screen coordinate mapping.
    """
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize calibrator.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration_points = []
        self.screen_points = []
        self.transform_matrix = None
        
    def add_calibration_point(self, camera_pos: Tuple[float, float], 
                             screen_pos: Tuple[int, int]):
        """
        Add a calibration point pair.
        
        Args:
            camera_pos: Position in camera coordinates
            screen_pos: Corresponding screen position
        """
        self.calibration_points.append(camera_pos)
        self.screen_points.append(screen_pos)
        logger.info(f"Added calibration point: {camera_pos} -> {screen_pos}")
    
    def compute_transform(self) -> bool:
        """
        Compute transformation matrix from calibration points.
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.calibration_points) < 4:
            logger.error("Need at least 4 calibration points")
            return False
        
        try:
            src_points = np.float32(self.calibration_points[:4])
            dst_points = np.float32(self.screen_points[:4])
            
            self.transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            logger.info("Calibration transform computed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to compute transform: {e}")
            return False
    
    def map_to_screen(self, camera_pos: Tuple[float, float]) -> Tuple[int, int]:
        """
        Map camera coordinates to screen coordinates.
        
        Args:
            camera_pos: Position in camera space
            
        Returns:
            Screen coordinates (x, y)
        """
        if self.transform_matrix is None:
            # Simple linear mapping as fallback
            x = int(camera_pos[0] / 640 * self.screen_width)
            y = int(camera_pos[1] / 480 * self.screen_height)
            return (x, y)
        
        # Apply perspective transform
        point = np.array([[[camera_pos[0], camera_pos[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.transform_matrix)
        
        x = int(transformed[0][0][0])
        y = int(transformed[0][0][1])
        
        # Clamp to screen bounds
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        return (x, y)
    
    def run_wizard(self, camera_capture) -> bool:
        """
        Run interactive calibration wizard.
        
        Args:
            camera_capture: CameraCapture instance
            
        Returns:
            True if calibration successful
        """
        logger.info("Starting calibration wizard...")
        
        # Define calibration target positions (corners + center)
        targets = [
            (50, 50, "Top-Left"),
            (self.screen_width - 50, 50, "Top-Right"),
            (self.screen_width - 50, self.screen_height - 50, "Bottom-Right"),
            (50, self.screen_height - 50, "Bottom-Left"),
        ]
        
        print("\n=== AeroControl Calibration Wizard ===")
        print("Point your index finger at each target and press SPACE")
        print("Press ESC to cancel\n")
        
        from .detector import HandDetector
        from .tracker import HandTracker
        
        detector = HandDetector()
        tracker = HandTracker()
        
        for target_x, target_y, target_name in targets:
            print(f"Point at {target_name} corner and press SPACE...")
            
            while True:
                ret, frame = camera_capture.read()
                if not ret:
                    continue
                
                # Detect hand
                hands_data = detector.detect(frame)
                primary_hand = tracker.update(hands_data)
                
                if primary_hand:
                    # Draw hand landmarks
                    frame = detector.draw_landmarks(frame, [primary_hand])
                    
                    # Get index finger position
                    index_tip = primary_hand['landmarks'][8]
                    camera_pos = (index_tip['x'], index_tip['y'])
                    
                    # Draw crosshair
                    cv2.circle(frame, (int(camera_pos[0]), int(camera_pos[1])), 
                              10, (0, 255, 0), 2)
                
                # Draw target indicator
                cv2.putText(frame, f"Point at: {target_name}", (20, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow("Calibration", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    cv2.destroyAllWindows()
                    return False
                elif key == 32:  # SPACE
                    if primary_hand:
                        self.add_calibration_point(camera_pos, (target_x, target_y))
                        break
        
        cv2.destroyAllWindows()
        
        # Compute transformation
        success = self.compute_transform()
        
        if success:
            print("\n✓ Calibration complete!")
        else:
            print("\n✗ Calibration failed")
        
        detector.close()
        return success