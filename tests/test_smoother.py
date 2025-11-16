"""
Unit tests for smoother module.
"""

import pytest
import numpy as np
from aerocontrol.smoother import AdaptiveSmoother, KalmanSmoother


class TestAdaptiveSmoother:
    """Test adaptive smoothing algorithm."""
    
    def test_initialization(self):
        """Test smoother initialization."""
        smoother = AdaptiveSmoother(alpha_base=0.3)
        assert smoother.alpha_base == 0.3
        assert smoother.smoothed_pos is None
    
    def test_first_position(self):
        """Test that first position is returned as-is."""
        smoother = AdaptiveSmoother()
        pos = smoother.smooth((100.0, 200.0), hand_scale=150.0)
        assert pos == (100.0, 200.0)
    
    def test_smoothing_effect(self):
        """Test that smoothing reduces movement."""
        smoother = AdaptiveSmoother(alpha_base=0.3)
        
        # First position
        pos1 = smoother.smooth((100.0, 100.0), hand_scale=150.0)
        
        # Large jump
        pos2 = smoother.smooth((200.0, 200.0), hand_scale=150.0)
        
        # Should be smoothed (not at target yet)
        assert pos2[0] < 200.0
        assert pos2[1] < 200.0
        assert pos2[0] > 100.0
        assert pos2[1] > 100.0
    
    def test_adaptive_behavior(self):
        """Test that smoothing adapts to hand distance."""
        smoother = AdaptiveSmoother(alpha_base=0.5, adaptation_factor=0.5)
        
        # Initialize
        smoother.smooth((100.0, 100.0), hand_scale=150.0)
        
        # Far hand (small scale) should have higher alpha
        pos_far = smoother.smooth((200.0, 200.0), hand_scale=50.0)
        alpha_far = smoother.get_current_alpha()
        
        # Reset
        smoother.reset()
        smoother.smooth((100.0, 100.0), hand_scale=150.0)
        
        # Near hand (large scale) should have lower alpha
        pos_near = smoother.smooth((200.0, 200.0), hand_scale=300.0)
        alpha_near = smoother.get_current_alpha()
        
        assert alpha_far > alpha_near
    
    def test_reset(self):
        """Test smoother reset."""
        smoother = AdaptiveSmoother()
        smoother.smooth((100.0, 100.0), hand_scale=150.0)
        assert smoother.smoothed_pos is not None
        
        smoother.reset()
        assert smoother.smoothed_pos is None


class TestKalmanSmoother:
    """Test Kalman filter smoothing."""
    
    def test_initialization(self):
        """Test Kalman filter initialization."""
        kalman = KalmanSmoother()
        assert kalman.state is None
    
    def test_first_measurement(self):
        """Test first measurement."""
        kalman = KalmanSmoother()
        pos = kalman.smooth((100.0, 200.0))
        assert pos == (100.0, 200.0)
    
    def test_filtering(self):
        """Test that Kalman filter smooths measurements."""
        kalman = KalmanSmoother(process_noise=0.01, measurement_noise=1.0)
        
        # Add measurements with noise
        measurements = [(100.0, 100.0), (105.0, 95.0), (110.0, 105.0)]
        filtered = []
        
        for meas in measurements:
            pos = kalman.smooth(meas)
            filtered.append(pos)
        
        # Filtered values should be smoother than raw measurements
        # (variance should be lower)
        raw_var = np.var([m[0] for m in measurements])
        filtered_var = np.var([f[0] for f in filtered])
        
        assert filtered_var < raw_var or len(filtered) < 3  # May need more samples