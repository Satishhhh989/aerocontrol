import logging
from typing import Optional, List
import numpy as np


logger = logging.getLogger(__name__)


class HandTracker:
    """
    Tracks the primary hand for cursor control.
    Implements stable hand selection to avoid jitter.
    """
    
    def __init__(self, stability_frames: int = 5):
        """
        Initialize hand tracker.
        
        Args:
            stability_frames: Number of frames to confirm hand switch
        """
        self.stability_frames = stability_frames
        self.primary_hand_id = None
        self.candidate_hand_id = None
        self.candidate_count = 0
        self.last_position = None
    
    def update(self, hands_data: Optional[List[dict]]) -> Optional[dict]:
        """
        Update tracker with new hand data and return primary hand.
        
        Args:
            hands_data: List of detected hands
            
        Returns:
            Primary hand data or None
        """
        if not hands_data:
            # No hands detected
            if self.primary_hand_id is not None:
                logger.debug("Lost primary hand")
            self.primary_hand_id = None
            self.candidate_hand_id = None
            self.candidate_count = 0
            return None
        
        # For simplicity, use the first detected hand as primary
        # In production, could use handedness preference or position tracking
        current_hand = hands_data[0]
        current_id = id(current_hand)
        
        if self.primary_hand_id is None:
            # No primary hand, establish one immediately
            self.primary_hand_id = current_id
            logger.debug("Primary hand established")
            return current_hand
        
        # Check if same hand is still present
        if current_id == self.primary_hand_id:
            self.candidate_count = 0
            return current_hand
        
        # Different hand detected - require stability before switching
        if current_id == self.candidate_hand_id:
            self.candidate_count += 1
            if self.candidate_count >= self.stability_frames:
                logger.debug("Switched to new primary hand")
                self.primary_hand_id = current_id
                self.candidate_hand_id = None
                self.candidate_count = 0
                return current_hand
        else:
            self.candidate_hand_id = current_id
            self.candidate_count = 1
        
        # Return current primary hand data (find it in hands_data)
        # For simplicity, return first hand
        return hands_data[0]
    
    def get_index_fingertip(self, hand_data: dict) -> tuple:
        """
        Get index fingertip position.
        
        Args:
            hand_data: Hand data dictionary
            
        Returns:
            (x, y) coordinates
        """
        # Index finger tip is landmark 8
        index_tip = hand_data['landmarks'][8]
        return (index_tip['x'], index_tip['y'])
    
    def get_velocity(self, current_pos: tuple, dt: float) -> float:
        """
        Calculate velocity between frames.
        
        Args:
            current_pos: Current (x, y) position
            dt: Time delta in seconds
            
        Returns:
            Velocity in pixels per second
        """
        if self.last_position is None or dt <= 0:
            self.last_position = current_pos
            return 0.0
        
        dx = current_pos[0] - self.last_position[0]
        dy = current_pos[1] - self.last_position[1]
        distance = np.sqrt(dx**2 + dy**2)
        
        velocity = distance / dt
        self.last_position = current_pos
        
        return velocity