"""
Gesture recognition module.
Detects pinch, swipe, and other hand gestures with state machine logic.
"""

import logging
import time
import numpy as np
from typing import Optional, Tuple
from enum import Enum


logger = logging.getLogger(__name__)


class GestureType(Enum):
    """Gesture types."""
    NONE = 0
    PINCH = 1  # Index + thumb
    RIGHT_CLICK = 2  # Two-finger pinch
    DRAG = 3  # Pinch + move
    ZOOM = 4  # Spread fingers
    SWIPE_UP = 5  # Four-finger swipe up
    SWIPE_DOWN = 6  # Four-finger swipe down
    PALM_OPEN = 7  # Pause gesture


class GestureRecognizer:
    """
    Recognizes hand gestures with debouncing and state machine logic.
    """
    
    def __init__(self, config: dict):
        """
        Initialize gesture recognizer.
        
        Args:
            config: Configuration dictionary with thresholds
        """
        self.config = config
        
        # Pinch thresholds
        self.pinch_threshold = config.get('pinch_threshold', 40)
        self.pinch_debounce = config.get('pinch_debounce_ms', 200) / 1000.0
        
        # Swipe thresholds
        self.swipe_min_distance = config.get('swipe_min_distance', 100)
        self.swipe_min_velocity = config.get('swipe_min_velocity', 200)
        self.swipe_debounce = config.get('swipe_debounce_ms', 500) / 1000.0
        
        # Zoom threshold
        self.zoom_threshold = config.get('zoom_threshold', 200)
        
        # State tracking
        self.current_gesture = GestureType.NONE
        self.last_gesture_time = 0
        self.is_pinching = False
        self.is_dragging = False
        
        # Swipe state machine
        self.swipe_start_y = None
        self.swipe_start_time = None
        self.swipe_active = False
        
        logger.info("Gesture recognizer initialized")
    
    def recognize(self, hand_data: dict, dt: float) -> Tuple[GestureType, dict]:
        """
        Recognize gesture from hand landmarks.
        
        Args:
            hand_data: Hand data with landmarks
            dt: Time delta since last frame
            
        Returns:
            Tuple of (gesture_type, gesture_data)
        """
        landmarks = hand_data['landmarks']
        current_time = time.time()
        
        # Extract key landmarks
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        # Check for palm open (all fingers extended)
        if self._is_palm_open(landmarks):
            return GestureType.PALM_OPEN, {}
        
        # Check for four-finger swipe (desktop switching)
        swipe_gesture = self._check_four_finger_swipe(landmarks, current_time)
        if swipe_gesture != GestureType.NONE:
            return swipe_gesture, {}
        
        # Check for pinch (index + thumb)
        pinch_dist = self._distance(thumb_tip, index_tip)
        
        if pinch_dist < self.pinch_threshold:
            # Debounce pinch detection
            if not self.is_pinching:
                if current_time - self.last_gesture_time > self.pinch_debounce:
                    self.is_pinching = True
                    self.last_gesture_time = current_time
                    logger.debug("Pinch detected")
                    return GestureType.PINCH, {'position': (index_tip['x'], index_tip['y'])}
            else:
                # Check if dragging
                self.is_dragging = True
                return GestureType.DRAG, {'position': (index_tip['x'], index_tip['y'])}
        else:
            # Release pinch
            if self.is_pinching:
                self.is_pinching = False
                self.is_dragging = False
                logger.debug("Pinch released")
        
        # Check for right-click (thumb + middle finger)
        middle_dist = self._distance(thumb_tip, middle_tip)
        if middle_dist < self.pinch_threshold:
            if current_time - self.last_gesture_time > self.pinch_debounce:
                self.last_gesture_time = current_time
                logger.debug("Right-click detected")
                return GestureType.RIGHT_CLICK, {}
        
        # Check for zoom (spread fingers)
        spread_dist = self._distance(thumb_tip, pinky_tip)
        if spread_dist > self.zoom_threshold:
            return GestureType.ZOOM, {'spread': spread_dist}
        
        return GestureType.NONE, {}
    
    def _distance(self, point1: dict, point2: dict) -> float:
        """Calculate Euclidean distance between two points."""
        dx = point1['x'] - point2['x']
        dy = point1['y'] - point2['y']
        return np.sqrt(dx**2 + dy**2)
    
    def _is_palm_open(self, landmarks: list) -> bool:
        """
        Check if palm is open (all fingers extended).
        Uses simple heuristic: all fingertips above their respective MCP joints.
        """
        # Fingertip and MCP (knuckle) indices
        finger_tips = [8, 12, 16, 20]  # Index, middle, ring, pinky
        finger_mcps = [5, 9, 13, 17]
        
        extended_count = 0
        for tip_idx, mcp_idx in zip(finger_tips, finger_mcps):
            if landmarks[tip_idx]['y'] < landmarks[mcp_idx]['y'] - 20:
                extended_count += 1
        
        # Consider palm open if at least 3 fingers extended
        return extended_count >= 3
    
    def _check_four_finger_swipe(self, landmarks: list, current_time: float) -> GestureType:
        """
        Detect four-finger vertical swipe for desktop switching.
        Uses state machine with hysteresis to avoid false positives.
        """
        # Get average Y position of four fingertips
        finger_tips = [8, 12, 16, 20]
        avg_y = sum(landmarks[i]['y'] for i in finger_tips) / len(finger_tips)
        
        # Check if four fingers are detected and relatively aligned
        # (simple heuristic: variance in Y position is low)
        y_positions = [landmarks[i]['y'] for i in finger_tips]
        y_variance = np.var(y_positions)
        
        if y_variance > 400:  # Fingers not aligned
            self._reset_swipe_state()
            return GestureType.NONE
        
        # Start swipe tracking
        if not self.swipe_active:
            self.swipe_start_y = avg_y
            self.swipe_start_time = current_time
            self.swipe_active = True
            return GestureType.NONE
        
        # Check swipe distance and velocity
        displacement = avg_y - self.swipe_start_y
        elapsed = current_time - self.swipe_start_time
        
        if elapsed < 0.1:  # Need minimum time to establish velocity
            return GestureType.NONE
        
        velocity = abs(displacement) / elapsed
        
        # Detect swipe up or down
        if abs(displacement) > self.swipe_min_distance and velocity > self.swipe_min_velocity:
            if current_time - self.last_gesture_time > self.swipe_debounce:
                self.last_gesture_time = current_time
                self._reset_swipe_state()
                
                if displacement < 0:  # Moving up
                    logger.info("Swipe UP detected for desktop switch")
                    return GestureType.SWIPE_UP
                else:  # Moving down
                    logger.info("Swipe DOWN detected for desktop switch")
                    return GestureType.SWIPE_DOWN
        
        return GestureType.NONE
    
    def _reset_swipe_state(self):
        """Reset swipe state machine."""
        self.swipe_start_y = None
        self.swipe_start_time = None
        self.swipe_active = False