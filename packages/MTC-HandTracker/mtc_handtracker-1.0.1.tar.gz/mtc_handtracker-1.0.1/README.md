<div align="center">

# 🖐️ HandTracker API
### The Professional Hand Tracking Engine for Robotics

<!-- DYNAMIC BADGES -->
<a href="https://github.com/BTech-Robotics-Club/Hand-Tracking/releases">
  <img src="https://img.shields.io/github/v/release/BTech-Robotics-Club/Hand-Tracking?style=for-the-badge&color=A8C7FA&labelColor=202124" alt="Latest Release">
</a>
<a href="https://pypi.org/project/MTC-HandTracker/">
  <img src="https://img.shields.io/pypi/v/MTC-HandTracker?style=for-the-badge&logo=pypi&labelColor=202124&logoColor=white&color=3775A9" alt="PyPI">
</a>
<a href="https://BTech-Robotics-Club.github.io/Hand-Tracking/">
  <img src="https://img.shields.io/badge/docs-read_live_site-6DD58C?style=for-the-badge&logo=materialdesign&labelColor=202124&logoColor=white" alt="Read Docs">
</a>
<a href="https://github.com/BTech-Robotics-Club/Hand-Tracking/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/license-AGPL_v3-E6C449?style=for-the-badge&logo=gnu&labelColor=202124&logoColor=white" alt="License">
</a>

<br>

<p align="center">
  <b>Stabilized. Normalized. Thread-Safe.</b><br>
  The "Batteries Included" computer vision layer for your robot arm.
</p>

</div>

---

## Overview

The **HandTrackingModule** wraps Google MediaPipe into a robust tool designed specifically for control loops. It solves the hard computer vision problems so you can focus on logic.

| Feature | Description |
| :--- | :--- |
| **Smoothing** | Built-in jitter reduction filters (EMA) prevent robot motors from shaking. |
| **Normalization** | Maps coordinates to your specific workspace (0.0 - 1.0), not the full webcam view. |
| **Asynchronous** | Heavy inference runs on a background thread to keep your main loop fast. |
| **Data-Driven** | define gestures in `gestures.yaml` instead of writing Python code. |

---

## License

**Copyright © 2025 by Majd Aburas for McMaster Technology Club**

This software is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

* **Open Source:** You can use, modify, and distribute this software.
* **Viral:** If you use this library in your application (even over a network), **you must open-source your entire application** under AGPL-3.0.
* **Closed Source / Commercial:** You cannot use this in a closed-source or proprietary commercial product without releasing your own source code.

For a proprietary commercial license, please contact **Majd Aburas** or the **McMaster Technology Club**.

---

## Installation

### Stable Release (Recommended)
Install the latest stable version directly from PyPI:

```bash
pip install MTC-HandTracker
```

### Bleeding Edge (Development)
If you need the latest changes from the main branch before they are released:

```bash
pip install git+https://github.com/McMaster-Technology-Club/Hand-Tracking.git
```

---

## Quick Start

Copy this code into `app.py`. It opens the camera and prints 6 real-time metrics.

```python
import cv2
from hand_tracker import HandTrackingModule

# 1. Initialize (High smoothing for robots)
tracker = HandTrackingModule(smoothing_factor=0.6)

# 2. Open Camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Flip for mirror view
    frame = cv2.flip(frame, 1)

    # 3. Process Frame (Returns a Tuple of 6)
    img, gesture, points, ratios, pinch, hands = tracker.process_frame(frame)

    # 4. Use Data
    if gesture == "PINCH":
        print(f"Pinching! Distance: {pinch:.2f}")
    
    # Draw
    cv2.putText(img, f"Gesture: {gesture}", (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Hand Tracker", img)
    
    if cv2.waitKey(1) == ord('q'): break

tracker.close()
cap.release()
cv2.destroyAllWindows()
```

---

## API Reference

### `HandTrackingModule(...)`
The main controller class.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `smoothing_factor` | `float` | `0.5` | Blend factor. `0.1` is slow/smooth. `0.9` is fast/jittery. |
| `min_detection_confidence` | `float` | `0.5` | AI confidence threshold. Increase if seeing ghosts. |
| `gestures_file` | `str` | `None` | Path to custom YAML file for overrides. |

### `process_frame(image) -> tuple`
Returns a **tuple of 6 values** describing the current frame.

| # | Name | Type | Description |
| :--- | :--- | :--- | :--- |
| **0** | `annotated_image` | `numpy` | Debug image with skeletons drawn. |
| **1** | `gesture` | `str` | Name of the gesture (e.g. `"FIST"`). |
| **2** | `norm_points` | `list` | (x,y) coordinates mapped to **calibration zone**. |
| **3** | `ratios` | `list` | Finger straightness (0.0 curled - 1.0 straight). |
| **4** | `pinch_metric` | `float` | Thumb-Index distance. `< 0.25` is touching. |
| **5** | `handedness` | `list` | List of hands seen: `["Right", "Left"]`. |

---

## Configuration

You don't need to write Python to make new gestures. The library uses **YAML** configuration files.

> **Pro Tip:** Run `HandTrackingModule.create_default_configs()` in your python script once. It will generate these files in your folder so you can edit them!

### 1. `gestures.yaml` (Example)
Define what a hand shape looks like.

```yaml
VULCAN_SALUTE:
  # Finger State: [Thumb, Index, Middle, Ring, Pinky]
  # 1 = UP, 0 = DOWN
  pattern: [1, 1, 0, 0, 1]
  
  # Optional: Require hand to point UP
  direction: "UP"
  direction_finger: "INDEX"
```

### 2. `calibration.yaml` (Example)
Define your robot's "Work Area".

```yaml
# Only track the center of the desk
# 0.0 is top/left, 1.0 is bottom/right
top_left: [0.2, 0.2]
bottom_right: [0.8, 0.8]
```

---

<div align="center">

**Built by the McMaster Technology Club**

[Report Bug](https://github.com/BTech-Robotics-Club/Hand-Tracking/issues) • [Request Feature](https://github.com/BTech-Robotics-Club/Hand-Tracking/issues)

</div>
