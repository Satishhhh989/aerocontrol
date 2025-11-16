# AeroControl - Design Document

This document explains the technical design decisions, algorithms, and parameters used in AeroControl.

## Architecture Overview

AeroControl follows a modular pipeline architecture:
Camera → Detector → Tracker → Gesture → Smoother → HID Emitter
↓
Calibrator

Each module is independent and testable, with clean interfaces.

## Smoothing Algorithm

### Exponential Moving Average (EMA)

We use EMA as the default smoothing method due to its simplicity and efficiency:
smoothed[t] = alpha * raw[t] + (1 - alpha) * smoothed[t-1]

Where:
- `alpha`: Smoothing factor (0-1)
- Lower alpha = more smoothing (slower response)
- Higher alpha = less smoothing (faster response)

### Adaptive Smoothing

The key innovation is **distance-based adaptive smoothing**:
scale_ratio = reference_hand_size / current_hand_size
scale_factor = 1.0 - scale_ratio
alpha_adaptive = alpha_base * (1.0 + k * scale_factor)
alpha_clamped = clamp(alpha_adaptive, alpha_min, alpha_max)

**Rationale:**
- When hand is **far** (small in frame): Need more responsiveness → higher alpha → less smoothing
- When hand is **near** (large in frame): Need more stability → lower alpha → more smoothing

This prevents jitter from small hand movements when close to camera while maintaining responsiveness when far away.

### Parameter Defaults
```yaml
alpha_base: 0.3           # Base smoothing factor
alpha_min: 0.1            # Minimum (far hand)
alpha_max: 0.7            # Maximum (near hand)
adaptation_factor: 0.5    # Strength of adaptation
reference_hand_size: 150  # Pixels (wrist to middle fingertip)
```

**Tuning Guide:**
- Increase `alpha_base` for faster cursor, decrease for smoother
- Adjust `adaptation_factor` to control how strongly distance affects smoothing
- Set `reference_hand_size` based on your camera and typical hand distance

### Alternative: Kalman Filter

An optional Kalman filter implementation is provided for advanced users:
```python
# State vector: [x, y, vx, vy]
# Process model: constant velocity
# Measurement: [x, y]
```

Kalman provides optimal smoothing under Gaussian noise assumptions but requires more tuning. Use EMA for most cases.

## Velocity Control

### Non-Linear Sensitivity Curve

Cursor speed is mapped using a power function:
cursor_delta = sign(velocity) * (|velocity| ** gamma) * gain

Where:
- `velocity`: Fingertip velocity in camera space (px/s)
- `gamma`: Power exponent (< 1 for compression, > 1 for expansion)
- `gain`: Scaling factor

**Default Parameters:**
```yaml
gamma: 0.6     # Compress high velocities
gain: 0.0025   # Scaling factor
min_velocity: 10  # Dead zone threshold
```

**Rationale:**
- `gamma < 1` compresses high velocities, allowing fine control at low speeds while still enabling fast cursor travel
- This mimics mouse acceleration curves in modern desktop environments
- Dead zone (`min_velocity`) prevents micro-jitter from affecting cursor

### Auto-Tuning (Future Enhancement)

Gain can be automatically tuned based on screen size:
optimal_gain = screen_diagonal / (reference_hand_size * scaling_factor)

## Gesture Detection

### Pinch Detection

Pinch is detected when thumb-index distance falls below threshold:
```python
distance = sqrt((thumb.x - index.x)^2 + (thumb.y - index.y)^2)
is_pinch = distance < pinch_threshold
```

**Default threshold:** 40 pixels

**Debouncing:** 200ms cooldown between pinch events to prevent double-clicks.

### Four-Finger Swipe State Machine

Desktop switching uses a robust state machine:
States:

IDLE: No swipe detected
TRACKING: Four fingers detected, tracking movement
FIRED: Swipe completed, in cooldown

Transitions:

IDLE → TRACKING: Four fingers with low Y-variance
TRACKING → FIRED: |displacement| > min_distance AND velocity > min_velocity
FIRED → IDLE: After debounce period


**Thresholds:**
```yaml
swipe_min_distance: 100 px   # Minimum vertical travel
swipe_min_velocity: 200 px/s # Minimum speed
swipe_debounce_ms: 500       # Cooldown period
```

**Anti-False-Positive Measures:**
1. Check Y-variance of four fingertips (< 400 px^2) to ensure fingers are aligned
2. Require both distance AND velocity thresholds to be met
3. Long debounce period (500ms) to prevent accidental multiple switches

### Palm Open Detection

Heuristic: Consider palm open if at least 3 of 4 fingers (index, middle, ring, pinky) have their tips above their MCP joints (knuckles) by > 20 pixels.

This gesture pauses cursor movement, useful for resting hand or repositioning.

## Coordinate Mapping

### Calibration Transform

We use a perspective transform to map camera coordinates to screen coordinates:
[x_screen]     [camera_x]
[y_screen]  =  T * [camera_y]
[   1    ]     [    1    ]

Where `T` is a 3x3 perspective transformation matrix computed from 4 calibration points using OpenCV's `getPerspectiveTransform`.

**Calibration Points:**
- Top-left corner
- Top-right corner
- Bottom-right corner
- Bottom-left corner

**Fallback:** If no calibration is performed, simple linear scaling is used:
x_screen = (x_camera / camera_width) * screen_width
y_screen = (y_camera / camera_height) * screen_height

## HID Event Emission

### Preferred: uinput

`uinput` creates a virtual HID device at the kernel level:
```python
device = uinput.Device([
    uinput.BTN_LEFT,
    uinput.BTN_RIGHT,
    uinput.REL_X,
    uinput.REL_Y,
    uinput.REL_WHEEL
])

device.emit(uinput.BTN_LEFT, 1)  # Press
device.emit(uinput.BTN_LEFT, 0)  # Release
```

**Advantages:**
- Low latency
- Works with all applications
- No X11 dependency

**Requirements:**
- `/dev/uinput` access
- `python-uinput` package
- User in `input` group or udev rules

### Fallback: pyautogui

If uinput is unavailable, fall back to `pyautogui`:
```python
import pyautogui
pyautogui.moveTo(x, y, duration=0)
pyautogui.click(button='left')
```

**Desktop Switching Fallback:**
- `wmctrl -s <N>`: EWMH-compliant (most window managers)
- `xdotool set_desktop <N>`: Alternative if wmctrl unavailable

## Performance Optimizations

1. **Frame Skipping:** Process every Nth frame if CPU-bound
2. **Resolution Scaling:** Lower camera resolution for faster processing
3. **MediaPipe Model Complexity:** Use `model_complexity=0` for speed
4. **Numpy Vectorization:** All math operations use numpy for speed
5. **Minimal Memory Allocation:** Reuse arrays where possible

## Testing Strategy

### Unit Tests

- **test_smoother.py**: Verifies EMA math, adaptive behavior, reset functionality
- **test_gesture.py**: Tests gesture detection logic, debouncing, state transitions

### Integration Tests

- **test_integration.py**: End-to-end pipeline with synthetic data
  - Cursor movement through tracker + smoother
  - Gesture sequences (swipe, pinch)
  - Ensures modules work together correctly

### Manual Testing Scenarios

1. **Normal Operation:** 30 FPS webcam, well-lit room
2. **Low Light:** Reduced detection accuracy expected
3. **No Root:** Fallback to pyautogui
4. **Desktop Switching:** Consistent 5-swipe test

## Future Enhancements

1. **Machine Learning Gesture Classification:** Train custom gesture recognizer
2. **Multi-Hand Gestures:** Two-hand controls for advanced actions
3. **Depth Camera Support:** Use RealSense or similar for true 3D tracking
4. **Wayland Support:** Implement ydotool or libei integration
5. **Custom Gesture Recording:** Allow users to record and recognize custom gestures

## References

- [MediaPipe Hands](https://google.github.io/mediapipe/solutions/hands.html)
- [Linux uinput Documentation](https://www.kernel.org/doc/html/latest/input/uinput.html)
- [Kalman Filtering Theory](https://www.kalmanfilter.net/)
- [EWMH Specification](https://specifications.freedesktop.org/wm-spec/wm-spec-latest.html)

---

**Version:** 1.0.0  
**Last Updated:** 2024