"""
Unit tests for gesture recognition.
"""

import pytest
from aerocontrol.gesture import GestureRecognizer, GestureType


class TestGestureRecognizer:
    """Test gesture recognition."""
    
    @pytest.fixture
    def config(self):
        """Default configuration for testing."""
        return {
            'pinch_threshold': 40,
            'pinch_debounce_ms': 100,
            'swipe_min_distance': 100,
            'swipe_min_velocity': 200,
            'swipe_debounce_ms': 300,
            'zoom_threshold': 200
        }
    
    @pytest.fixture
    def recognizer(self, config):
        """Create gesture recognizer."""
        return GestureRecognizer(config)
    
    def create_hand_data(self, thumb_pos, index_pos, middle_pos=(0, 0), 
                        ring_pos=(0, 0), pinky_pos=(0, 0)):
        """Helper to create hand landmark data."""
        landmarks = []
        
        # Add all 21 landmarks (simplified)
        for i in range(21):
            if i == 4:  # Thumb tip
                landmarks.append({'x': thumb_pos[0], 'y': thumb_pos[1], 'z': 0})
            elif i == 8:  # Index tip
                landmarks.append({'x': index_pos[0], 'y': index_pos[1], 'z': 0})
            elif i == 12:  # Middle tip
                landmarks.append({'x': middle_pos[0], 'y': middle_pos[1], 'z': 0})
            elif i == 16:  # Ring tip
                landmarks.append({'x': ring_pos[0], 'y': ring_pos[1], 'z': 0})
            elif i == 20:  # Pinky tip
                landmarks.append({'x': pinky_pos[0], 'y': pinky_pos[1], 'z': 0})
            else:
                landmarks.append({'x': 0, 'y': 0, 'z': 0})
        
        return {'landmarks': landmarks}
    
    def test_no_gesture(self, recognizer):
        """Test when no gesture is detected."""
        hand_data = self.create_hand_data(
            thumb_pos=(0, 0),
            index_pos=(100, 100)
        )
        
        gesture, data = recognizer.recognize(hand_data, dt=0.033)
        assert gesture == GestureType.NONE
    
    def test_pinch_detection(self, recognizer):
        """Test pinch gesture detection."""
        # Thumb and index close together
        hand_data = self.create_hand_data(
            thumb_pos=(100, 100),
            index_pos=(110, 105)  # Within threshold
        )
        
        gesture, data = recognizer.recognize(hand_data, dt=0.033)
        assert gesture == GestureType.PINCH
    
    def test_pinch_debounce(self, recognizer):
        """Test that pinch is debounced."""
        hand_data = self.create_hand_data(
            thumb_pos=(100, 100),
            index_pos=(110, 105)
        )
        
        # First pinch
        gesture1, _ = recognizer.recognize(hand_data, dt=0.033)
        
        # Immediate second attempt should be ignored or return DRAG
        gesture2, _ = recognizer.recognize(hand_data, dt=0.01)
        
        assert gesture1 == GestureType.PINCH
        # Second should be DRAG since pinch is held
        assert gesture2 in [GestureType.DRAG, GestureType.NONE]
    
    def test_right_click_detection(self, recognizer):
        """Test right-click gesture (thumb + middle)."""
        hand_data = self.create_hand_data(
            thumb_pos=(100, 100),
            index_pos=(200, 200),  # Far from thumb
            middle_pos=(110, 105)  # Close to thumb
        )
        
        gesture, data = recognizer.recognize(hand_data, dt=0.033)
        assert gesture == GestureType.RIGHT_CLICK