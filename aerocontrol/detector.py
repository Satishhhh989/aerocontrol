import cv2
import mediapipe as mp
import logging
from typing import Optional, List, Tuple
import numpy as np


logger = logging.getLogger(__name__)


class HandDetector:
    """
    Hand detection using MediaPipe Hands.
    """
    
    def __init__(self, max_hands: int = 2, min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5):
        """
        Initialize hand detector.
        
        Args:
            max_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
        """
        self.max_hands = max_hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils
        logger.info("Hand detector initialized")
    
    def detect(self, frame: np.ndarray) -> Optional[List[dict]]:
        """
        Detect hands in frame.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            List of hand data dictionaries or None if no hands detected
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        if not results.multi_hand_landmarks:
            return None
        
        hands_data = []
        frame_height, frame_width = frame.shape[:2]
        
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Extract landmark coordinates
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append({
                    'x': lm.x * frame_width,
                    'y': lm.y * frame_height,
                    'z': lm.z  # Relative depth
                })
            
            # Get handedness (left/right)
            handedness = "Right"
            if results.multi_handedness:
                handedness = results.multi_handedness[hand_idx].classification[0].label
            
            hands_data.append({
                'landmarks': landmarks,
                'handedness': handedness,
                'raw_landmarks': hand_landmarks
            })
        
        return hands_data
    
    def draw_landmarks(self, frame: np.ndarray, hands_data: List[dict]) -> np.ndarray:
        """
        Draw hand landmarks on frame.
        
        Args:
            frame: BGR image
            hands_data: List of hand data from detect()
            
        Returns:
            Frame with drawn landmarks
        """
        for hand_data in hands_data:
            self.mp_draw.draw_landmarks(
                frame,
                hand_data['raw_landmarks'],
                self.mp_hands.HAND_CONNECTIONS
            )
        return frame
    
    def get_hand_scale(self, landmarks: List[dict]) -> float:
        """
        Estimate hand scale based on wrist to middle finger distance.
        
        Args:
            landmarks: Hand landmarks
            
        Returns:
            Distance in pixels (proxy for hand-to-camera distance)
        """
        # Wrist (0) to middle finger tip (12)
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        
        dx = middle_tip['x'] - wrist['x']
        dy = middle_tip['y'] - wrist['y']
        
        return np.sqrt(dx**2 + dy**2)
    
    def close(self):
        """Release resources."""
        if self.hands:
            self.hands.close()
            logger.info("Hand detector closed")