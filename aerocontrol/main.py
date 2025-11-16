"""
Main controller for AeroControl.
Coordinates all components and implements the control loop.
"""

import logging
import time
import subprocess
from typing import Optional


logger = logging.getLogger(__name__)


class AeroControl:
    """
    Main controller that coordinates all components.
    """
    
    def __init__(self, camera_id: int, config: dict, debug: bool = False):
        """
        Initialize AeroControl.
        
        Args:
            camera_id: Camera device index
            config: Configuration dictionary
            debug: Enable debug UI
        """
        from .capture import CameraCapture
        from .detector import HandDetector
        from .tracker import HandTracker
        from .gesture import GestureRecognizer
        from .smoother import AdaptiveSmoother
        from .hidemitter import HIDEmitter
        from .calibrate import Calibrator
        from .ui_debug import DebugUI
        
        # Get screen resolution
        screen_width, screen_height = self._get_screen_resolution()
        
        # Initialize components
        cam_config = config.get('camera', {})
        self.camera = CameraCapture(
            camera_id=camera_id,
            width=cam_config.get('width', 640),
            height=cam_config.get('height', 480),
            fps=cam_config.get('fps', 30)
        )
        
        self.detector = HandDetector()
        self.tracker = HandTracker()
        self.gesture = GestureRecognizer(config.get('gestures', {}))
        
        smoother_config = config.get('smoother', {})
        self.smoother = AdaptiveSmoother(**smoother_config)
        
        self.hid = HIDEmitter(screen_width, screen_height)
        self.calibrator = Calibrator(screen_width, screen_height)
        
        self.debug_ui = DebugUI()
        if debug:
            self.debug_ui.enable()
        
        self.velocity_config = config.get('velocity', {})
        self.running = False
        self.is_dragging = False
        self.cursor_paused = False
        
        logger.info("AeroControl initialized")
    
    def _get_screen_resolution(self) -> tuple:
        """Get screen resolution using xrandr."""
        try:
            output = subprocess.check_output(['xrandr']).decode()
            for line in output.split('\n'):
                if '*' in line:
                    resolution = line.split()[0]
                    w, h = resolution.split('x')
                    return int(w), int(h)
        except:
            logger.warning("Could not detect screen resolution, using default 1920x1080")
        
        return 1920, 1080
    
    def run_calibration(self) -> bool:
        """Run calibration wizard."""
        if not self.camera.open():
            logger.error("Failed to open camera for calibration")
            return False
        
        success = self.calibrator.run_wizard(self.camera)
        self.camera.close()
        
        return success
    
    def run(self):
        """Main control loop."""
        if not self.camera.open():
            logger.error("Failed to open camera")
            return
        
        self.running = True
        last_time = time.time()
        
        logger.info("AeroControl started - Press Ctrl+C to stop")
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            # Read frame
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to read frame")
                continue
            
            # Detect hands
            hands_data = self.detector.detect(frame)
            
            # Track primary hand
            primary_hand = self.tracker.update(hands_data)
            
            if primary_hand is None:
                if self.debug_ui.enabled:
                    self._update_debug_ui(frame, {})
                continue
            
            # Get hand scale for adaptive smoothing
            hand_scale = self.detector.get_hand_scale(primary_hand['landmarks'])
            
            # Recognize gesture
            from .gesture import GestureType
            gesture_type, gesture_data = self.gesture.recognize(primary_hand, dt)
            
            # Handle palm open (pause)
            if gesture_type == GestureType.PALM_OPEN:
                self.cursor_paused = True
                if self.debug_ui.enabled:
                    self._update_debug_ui(frame, {
                        'fps': self.camera.get_fps(),
                        'gesture': 'PAUSED',
                        'hand_scale': hand_scale
                    })
                continue
            else:
                self.cursor_paused = False
            
            # Handle desktop switching gestures
            if gesture_type == GestureType.SWIPE_UP:
                self.hid.switch_desktop('previous')
                continue
            elif gesture_type == GestureType.SWIPE_DOWN:
                self.hid.switch_desktop('next')
                continue
            
            # Get index fingertip position
            index_tip_cam = self.tracker.get_index_fingertip(primary_hand)
            
            # Apply smoothing
            smoothed_cam = self.smoother.smooth(index_tip_cam, hand_scale)
            
            # Map to screen coordinates
            screen_pos = self.calibrator.map_to_screen(smoothed_cam)
            
            # Apply velocity-based control
            velocity = self.tracker.get_velocity(index_tip_cam, dt)
            adjusted_pos = self._apply_velocity_control(screen_pos, velocity)
            
            # Move cursor
            if not self.cursor_paused:
                self.hid.move_mouse(adjusted_pos[0], adjusted_pos[1])
            
            # Handle click gestures
            if gesture_type == GestureType.PINCH:
                if not self.is_dragging:
                    self.hid.click('left')
            elif gesture_type == GestureType.RIGHT_CLICK:
                self.hid.click('right')
            elif gesture_type == GestureType.DRAG:
                if not self.is_dragging:
                    self.hid.drag_start()
                    self.is_dragging = True
            elif gesture_type == GestureType.ZOOM:
                spread = gesture_data.get('spread', 0)
                scroll_amount = int((spread - 200) / 50)
                self.hid.scroll(scroll_amount)
            else:
                if self.is_dragging:
                    self.hid.drag_end()
                    self.is_dragging = False
            
            # Update debug UI
            if self.debug_ui.enabled:
                frame = self.detector.draw_landmarks(frame, [primary_hand])
                self._update_debug_ui(frame, {
                    'fps': self.camera.get_fps(),
                    'gesture': gesture_type.name,
                    'alpha': self.smoother.get_current_alpha(),
                    'hand_scale': hand_scale,
                    'cursor_x': adjusted_pos[0],
                    'cursor_y': adjusted_pos[1],
                    'cursor_cam_x': smoothed_cam[0],
                    'cursor_cam_y': smoothed_cam[1]
                })
    
    def _apply_velocity_control(self, position: tuple, velocity: float) -> tuple:
        """
        Apply velocity-based sensitivity curve.
        
        Formula: adjusted = pos + sign(v) * (|v| ** gamma) * gain
        """
        gamma = self.velocity_config.get('gamma', 0.6)
        gain = self.velocity_config.get('gain', 0.0025)
        min_vel = self.velocity_config.get('min_velocity', 10)
        
        if velocity < min_vel:
            return position
        
        # Apply power curve
        adjustment = (velocity ** gamma) * gain
        
        # For now, just return original position
        # In production, would calculate direction and apply adjustment
        return position
    
    def _update_debug_ui(self, frame, info: dict):
        """Update debug UI with current info."""
        self.debug_ui.draw(frame, info)
    
    def stop(self):
        """Stop AeroControl."""
        self.running = False
        self.camera.close()
        self.detector.close()
        self.hid.close()
        self.debug_ui.disable()
        logger.info("AeroControl stopped")