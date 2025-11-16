import numpy as np
import logging
from typing import Tuple, Optional


logger = logging.getLogger(__name__)


class AdaptiveSmoother:
    """
    Adaptive smoothing that adjusts based on hand distance.
    Uses Exponential Moving Average (EMA) by default.
    """
    
    def __init__(self, alpha_base: float = 0.3, alpha_min: float = 0.1,
                 alpha_max: float = 0.7, adaptation_factor: float = 0.5,
                 reference_hand_size: float = 150.0):
        """
        Initialize adaptive smoother.
        
        Args:
            alpha_base: Base EMA smoothing factor (0-1, lower = more smoothing)
            alpha_min: Minimum alpha value
            alpha_max: Maximum alpha value
            adaptation_factor: How strongly distance affects smoothing
            reference_hand_size: Reference hand size in pixels for normalization
        """
        self.alpha_base = alpha_base
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.adaptation_factor = adaptation_factor
        self.reference_hand_size = reference_hand_size
        
        self.smoothed_pos: Optional[np.ndarray] = None
        self.current_alpha = alpha_base
        
        logger.info(f"Smoother initialized: alpha={alpha_base}, "
                   f"range=[{alpha_min}, {alpha_max}]")
    
    def smooth(self, position: Tuple[float, float], hand_scale: float) -> Tuple[float, float]:
        """
        Apply adaptive smoothing to position.
        
        Formula: smoothed = alpha * current + (1 - alpha) * previous
        Alpha adapts based on hand scale: alpha = alpha_base * (1 + k*(1-s))
        where s = reference_size / current_size (normalized scale)
        
        Args:
            position: Current (x, y) position
            hand_scale: Current hand scale (pixels)
            
        Returns:
            Smoothed (x, y) position
        """
        pos_array = np.array(position, dtype=np.float32)
        
        # Initialize on first call
        if self.smoothed_pos is None:
            self.smoothed_pos = pos_array
            return tuple(self.smoothed_pos)
        
        # Calculate adaptive alpha based on hand scale
        # When hand is far (small scale), use higher alpha (less smoothing, more responsive)
        # When hand is near (large scale), use lower alpha (more smoothing, more stable)
        scale_ratio = self.reference_hand_size / max(hand_scale, 1.0)
        scale_factor = 1.0 - scale_ratio  # Negative when hand is far, positive when near
        
        self.current_alpha = self.alpha_base * (1.0 + self.adaptation_factor * scale_factor)
        self.current_alpha = np.clip(self.current_alpha, self.alpha_min, self.alpha_max)
        
        # Apply EMA smoothing
        self.smoothed_pos = (self.current_alpha * pos_array + 
                            (1.0 - self.current_alpha) * self.smoothed_pos)
        
        return tuple(self.smoothed_pos)
    
    def get_current_alpha(self) -> float:
        """Get current smoothing factor."""
        return self.current_alpha
    
    def reset(self):
        """Reset smoother state."""
        self.smoothed_pos = None
        self.current_alpha = self.alpha_base


class KalmanSmoother:
    """
    Kalman filter for advanced smoothing (optional alternative to EMA).
    """
    
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        """
        Initialize Kalman filter.
        
        Args:
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
        """
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        
        # State: [x, y, vx, vy]
        self.state = None
        self.covariance = None
        
    def smooth(self, measurement: Tuple[float, float]) -> Tuple[float, float]:
        """
        Apply Kalman filtering.
        
        Args:
            measurement: Measured (x, y) position
            
        Returns:
            Filtered (x, y) position
        """
        z = np.array([[measurement[0]], [measurement[1]]])
        
        if self.state is None:
            # Initialize state
            self.state = np.array([[measurement[0]], [measurement[1]], [0.0], [0.0]])
            self.covariance = np.eye(4) * 1.0
            return measurement
        
        # Prediction step
        F = np.array([[1, 0, 1, 0],
                     [0, 1, 0, 1],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])
        
        Q = np.eye(4) * self.process_noise
        
        self.state = F @ self.state
        self.covariance = F @ self.covariance @ F.T + Q
        
        # Update step
        H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]])
        
        R = np.eye(2) * self.measurement_noise
        
        y = z - H @ self.state
        S = H @ self.covariance @ H.T + R
        K = self.covariance @ H.T @ np.linalg.inv(S)
        
        self.state = self.state + K @ y
        self.covariance = (np.eye(4) - K @ H) @ self.covariance
        
        return (float(self.state[0, 0]), float(self.state[1, 0]))
    
    def reset(self):
        """Reset filter state."""
        self.state = None
        self.covariance = None