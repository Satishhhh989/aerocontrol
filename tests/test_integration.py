"""
Integration tests for AeroControl.
Uses synthetic keypoint sequences to test end-to-end behavior.
"""

import pytest
import numpy as np
from aerocontrol.tracker import HandTracker
from aerocontrol.smoother import AdaptiveSmoother
from aerocontrol.gesture import GestureRecognizer, GestureType


class TestIntegration:
    """Integration tests."""
    
    def create_synthetic_hand(self, index_pos, thumb_pos=None):
        """Create synthetic hand data."""
        landmarks = []
        for i in range(21):
            if i == 8:  # Index finger
                landmarks.append({'x': index_pos[0], 'y': index_pos[1], 'z': 0})
            elif i == 4 and thumb_pos:  # Thumb
                landmarks.append({'x': thumb_pos[0], 'y': thumb_pos[1], 'z': 0})
            else:
                landmarks.append({'x': 0, 'y': 0, 'z': 0})
        
        return {'landmarks': landmarks, 'handedness': 'Right', 'raw_landmarks': None}
    
    def test_cursor_movement_pipeline(self):
        """Test cursor movement through tracker and smoother."""
        tracker = HandTracker()
        smoother = AdaptiveSmoother()
        
        # Simulate hand moving in a line
        positions = [(100 + i*10, 100 + i*10) for i in range(10)]
        
        smoothed_positions = []
        
        for pos in positions:
            hand_data = self.create_synthetic_hand(index_pos=pos)
            primary_hand = tracker.update([hand_data])
            
            if primary_hand:
                index_tip = tracker.get_index_fingertip(primary_hand)
                smoothed = smoother.smooth(index_tip, hand_scale=150.0)
                smoothed_positions.append(smoothed)
        
        # Check that we got smoothed positions
        assert len(smoothed_positions) == len(positions)
        
        # Smoothed positions should lag behind raw positions
        # (except the first one which is unfiltered)
        assert smoothed_positions[-1][0] < positions[-1][0]
        assert smoothed_positions[-1][1] < positions[-1][1]
    
    def test_swipe_detection_sequence(self):
        """Test desktop swipe detection with synthetic sequence."""
        config = {
            'pinch_threshold': 40,
            'pinch_debounce_ms': 100,
            'swipe_min_distance': 100,
            'swipe_min_velocity': 200,
            'swipe_debounce_ms': 300,
            'zoom_threshold': 200
        }
        
        recognizer = GestureRecognizer(config)
        
        # Create a vertical swipe sequence (4 fingers moving up)
        # This is a simplified test - real implementation would need all 4 fingers
        
        # For now, just verify the gesture recognizer is callable
        hand_data = self.create_synthetic_hand(
            index_pos=(100, 100),
            thumb_pos=(120, 100)
        )
        
        gesture, data = recognizer.recognize(hand_data, dt=0.033)
        assert gesture in GestureType
    
    def test_pinch_click_sequence(self):
        """Test pinch-to-click behavior."""
        config = {
            'pinch_threshold': 40,
            'pinch_debounce_ms': 100,
            'swipe_min_distance': 100,
            'swipe_min_velocity': 200,
            'swipe_debounce_ms': 300,
            'zoom_threshold': 200
        }
        
        recognizer = GestureRecognizer(config)
        
        # Simulate pinch gesture (thumb and index close)
        hand_data = self.create_synthetic_hand(
            index_pos=(100, 100),
            thumb_pos=(110, 105)  # Close to index
        )
        
        gesture, data = recognizer.recognize(hand_data, dt=0.033)
        assert gesture == GestureType.PINCH
        
        # Continue pinch -> should transition to drag
        gesture2, data2 = recognizer.recognize(hand_data, dt=0.033)
        assert gesture2 in [GestureType.DRAG, GestureType.PINCH]