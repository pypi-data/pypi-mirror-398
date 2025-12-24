"""
File: detector.py
Author: Majd Aburas (Modified by Coding Partner)
Date: 2025-11-10
Description: A clean, asynchronous, OOP module for MediaPipe hand tracking,
             gesture detection, and perspective normalization.
             Now features Thread Safety, Smoothing, and Handedness.
"""
import cv2
import time
import yaml
import threading
import shutil
import os
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path
from types import SimpleNamespace

# --- PACKAGE PATH RESOLUTION ---
# Finds the directory where this installed file lives on the computer
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(MODULE_DIR, 'assets')

def _load_yaml(file_path: str) -> dict:
    try:
        with open(Path(file_path), 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: YAML file not found at {file_path}. Returning empty dict.")
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

class LandmarkSmoother:
    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.prev_landmarks = None

    def smooth(self, current_landmarks):
        if self.prev_landmarks is None:
            self.prev_landmarks = current_landmarks
            return current_landmarks

        smoothed_hand = []
        for i, curr in enumerate(current_landmarks):
            prev = self.prev_landmarks[i]
            new_x = prev.x + self.alpha * (curr.x - prev.x)
            new_y = prev.y + self.alpha * (curr.y - prev.y)
            new_z = prev.z + self.alpha * (curr.z - prev.z)
            smoothed_hand.append(SimpleNamespace(x=new_x, y=new_y, z=new_z))

        self.prev_landmarks = smoothed_hand
        return smoothed_hand

class HandTrackingModule:
    # --- Indices & Paths ---
    _FINGERTIP_INDICES = [4, 8, 12, 16, 20]
    _FINGER_MCP_INDICES = [2, 5, 9, 13, 17]
    _FINGER_PATHS = {
        "THUMB": [0, 1, 2, 3, 4], "INDEX": [0, 5, 6, 7, 8],
        "MIDDLE": [0, 9, 10, 11, 12], "RING": [0, 13, 14, 15, 16],
        "PINKY": [0, 17, 18, 19, 20]
    }
    _FINGER_NAMES = ["THUMB", "INDEX", "MIDDLE", "RING", "PINKY"]

    def __init__(self,
                 model_path: str = None,
                 num_hands: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 config_file: str = None,
                 gestures_file: str = None,
                 calibration_file: str = None,
                 smoothing_factor: float = 0.5):

        self.lock = threading.Lock()

        # --- 1. Path Resolution (THE FIX) ---
        # If user passes None, we construct the path to the bundled assets
        self.config_path = config_file if config_file else os.path.join(ASSETS_DIR, 'Configurations', 'config.yaml')
        self.gestures_path = gestures_file if gestures_file else os.path.join(ASSETS_DIR, 'Configurations', 'gestures.yaml')
        self.calib_path = calibration_file if calibration_file else os.path.join(ASSETS_DIR, 'Configurations', 'calibration.yaml')
        
        real_model_path = model_path if model_path else os.path.join(ASSETS_DIR, 'Models', 'hand_landmarker.task')

        # --- 2. Load Data ---
        self.config = _load_yaml(self.config_path)
        self.gestures = _load_yaml(self.gestures_path)
        self.calibration_points = _load_yaml(self.calib_path)
        
        self.draw_config = self.config.get('drawing', {})
        self.gesture_config = self.config.get('gestures', {})
        self.proximity_config = self.config.get('proximity_gestures', {})

        self.coeffs = {
            'thumb': self.gesture_config.get('thumb_coeff', 0.9),
            'index': self.gesture_config.get('index_coeff', 0.9),
            'middle': self.gesture_config.get('middle_coeff', 0.9),
            'ring': self.gesture_config.get('ring_coeff', 0.9),
            'pinky': self.gesture_config.get('pinky_coeff', 0.9)
        }
        self.pinch_threshold = self.proximity_config.get('pinch_threshold', 0.3)
        print(f"Loaded config from: {self.config_path}")

        # --- 3. Init State ---
        self.result = None
        self.annotated_image = None
        self.latest_frame = None
        self.current_gesture = "NONE"
        self.normalized_hands = []
        self.current_handedness = []
        self.last_timestamp_ms = 0
        self.current_finger_coeffs = [0.0] * 5
        self.pinch_metric = -1.0

        self.smoothers = {i: LandmarkSmoother(alpha=smoothing_factor) for i in range(num_hands)}

        # --- 4. Perspective Matrix ---
        self.perspective_matrix = None
        try:
            if 'top_left' in self.calibration_points:
                src_pts = np.float32([
                    self.calibration_points['top_left'], self.calibration_points['top_right'],
                    self.calibration_points['bottom_left'], self.calibration_points['bottom_right']
                ])
                dst_pts = np.float32([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
                self.perspective_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            else:
                print("Calibration points missing. Normalization disabled.")
        except Exception as e:
            print(f"Normalization disabled: {e}")

        # --- 5. MediaPipe Init ---
        try:
            options = vision.HandLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=real_model_path),
                running_mode=vision.RunningMode.LIVE_STREAM,
                num_hands=num_hands,
                min_hand_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                result_callback=self._callback
            )
            self.landmarker = vision.HandLandmarker.create_from_options(options)
            print(f"HandLandmarker initialized with model: {real_model_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize HandLandmarker.\nChecked path: {real_model_path}\nError: {e}")

    @staticmethod
    def create_default_configs(destination_dir="."):
        dest_path = Path(destination_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        files = {
            'config.yaml': 'my_config.yaml',
            'gestures.yaml': 'my_gestures.yaml',
            'calibration.yaml': 'my_calibration.yaml'
        }
        
        print(f"Generating default config files in '{destination_dir}'...")
        for internal_name, new_name in files.items():
            src = os.path.join(ASSETS_DIR, 'Configurations', internal_name)
            dst = dest_path / new_name
            try:
                shutil.copy(src, dst)
                print(f" - Created {new_name}")
            except Exception as e:
                print(f" - Failed to create {new_name}: {e}")
        print("Done.")

    def _callback(self, result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        with self.lock:
            self.result = result
            self.latest_frame = output_image.numpy_view().copy()
            annotated_image = self.latest_frame.copy()

            self.current_gesture = "NONE"
            self.normalized_hands = []
            self.current_handedness = []
            self.current_finger_coeffs = [0.0] * 5
            self.pinch_metric = -1.0

            if result.hand_landmarks:
                for hand_categories in result.handedness:
                    self.current_handedness.append(hand_categories[0].category_name)

                for i, hand_landmarks in enumerate(result.hand_landmarks):
                    smoothed_lm = self.smoothers[i].smooth(hand_landmarks) if i in self.smoothers else hand_landmarks
                    
                    self._draw_landmarks(annotated_image, smoothed_lm)
                    self._calculate_proximity(smoothed_lm)
                    
                    if i == 0:
                        self._detect_gestures(smoothed_lm)

                    if self.perspective_matrix is not None:
                        self._normalize_landmarks(smoothed_lm)

            self.annotated_image = annotated_image

    def _draw_landmarks(self, image, landmarks):
        cfg = self.draw_config
        l_color = tuple(cfg.get('landmark_color', [0, 255, 0]))
        c_color = tuple(cfg.get('connection_color', [255, 255, 255]))
        rad = cfg.get('radius', 5)
        thick = cfg.get('thickness', 2)
        h, w, _ = image.shape

        for conn in vision.HandLandmarksConnections.HAND_CONNECTIONS:
            start = landmarks[conn.start]
            end = landmarks[conn.end]
            cv2.line(image, (int(start.x*w), int(start.y*h)), (int(end.x*w), int(end.y*h)), c_color, thick)
        for lm in landmarks:
            cv2.circle(image, (int(lm.x*w), int(lm.y*h)), rad, l_color, -1)

    def _calculate_proximity(self, hand_landmarks):
        try:
            d_pinch = ((hand_landmarks[4].x-hand_landmarks[8].x)**2 + (hand_landmarks[4].y-hand_landmarks[8].y)**2)**0.5
            d_ref = ((hand_landmarks[5].x-hand_landmarks[17].x)**2 + (hand_landmarks[5].y-hand_landmarks[17].y)**2)**0.5
            self.pinch_metric = d_pinch / d_ref if d_ref > 1e-6 else -1.0
        except: self.pinch_metric = -1.0

    def _fingers_up(self, lm):
        fingers, coeffs = [], []
        try:
            for name in self._FINGER_NAMES:
                path = self._FINGER_PATHS[name]
                d_tip = ((lm[path[-1]].x - lm[path[0]].x)**2 + (lm[path[-1]].y - lm[path[0]].y)**2)**0.5
                d_path = sum([((lm[path[i]].x-lm[path[i+1]].x)**2 + (lm[path[i]].y-lm[path[i+1]].y)**2)**0.5 for i in range(len(path)-1)])
                ratio = d_tip / d_path if d_path > 1e-6 else 1.0
                coeffs.append(ratio)
                fingers.append(0 if ratio < self.coeffs[name.lower()] else 1)
        except: return [0]*5, [0.0]*5
        return fingers, coeffs
        
    def _check_direction(self, hand_landmarks: list, finger_name: str, req_direction: str) -> bool:
        finger_map = {
            "THUMB": (self._FINGERTIP_INDICES[0], self._FINGER_MCP_INDICES[0]),
            "INDEX": (self._FINGERTIP_INDICES[1], self._FINGER_MCP_INDICES[1]),
            "MIDDLE": (self._FINGERTIP_INDICES[2], self._FINGER_MCP_INDICES[2]),
            "RING": (self._FINGERTIP_INDICES[3], self._FINGER_MCP_INDICES[3]),
            "PINKY": (self._FINGERTIP_INDICES[4], self._FINGER_MCP_INDICES[4]),
        }
        finger_name_upper = finger_name.upper()
        if finger_name_upper not in finger_map: return False

        tip_idx, base_idx = finger_map[finger_name_upper]
        try:
            tip_lm = hand_landmarks[tip_idx]
            base_lm = hand_landmarks[base_idx]
            dx = tip_lm.x - base_lm.x
            dy = tip_lm.y - base_lm.y 
            dominance = 1.5

            if req_direction == "UP": return dy < 0 and abs(dy) > abs(dx) * dominance
            elif req_direction == "DOWN": return dy > 0 and abs(dy) > abs(dx) * dominance
            elif req_direction == "LEFT": return dx < 0 and abs(dx) > abs(dy) * dominance
            elif req_direction == "RIGHT": return dx > 0 and abs(dx) > abs(dy) * dominance
        except Exception: return False
        return False

    def _detect_gestures(self, lm):
        fingers, coeffs = self._fingers_up(lm)
        self.current_finger_coeffs = coeffs
        self.current_gesture = "UNKNOWN"
        for name, props in self.gestures.items():
            if not isinstance(props, dict): continue
            
            # Pattern
            if fingers != props.get('pattern'): continue

            # Direction
            req_direction = props.get('direction', 'ALL').upper()
            if req_direction != 'ALL':
                req_finger = props.get('direction_finger', 'NONE').upper()
                if (req_finger == 'NONE' or not self._check_direction(lm, req_finger, req_direction)):
                    continue
            
            # Proximity
            proximity_thresh = props.get('proximity_threshold')
            if proximity_thresh is not None:
                if (self.pinch_metric < 0 or self.pinch_metric >= proximity_thresh):
                    continue

            self.current_gesture = name
            return

    def _normalize_landmarks(self, lm):
        pts = np.float32([(l.x, l.y) for l in lm]).reshape(-1, 1, 2)
        warped = cv2.perspectiveTransform(pts, self.perspective_matrix)
        self.normalized_hands.append([tuple(p) for p in warped.squeeze()])

    def process_frame(self, image: np.ndarray):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        ts = int(time.time() * 1000)
        if ts <= self.last_timestamp_ms: ts = self.last_timestamp_ms + 1
        self.last_timestamp_ms = ts

        self.landmarker.detect_async(mp_image, ts)

        with self.lock:
            if self.annotated_image is None:
                return image, "INITIALIZING", [], [0.0]*5, -1.0, []
            return (self.annotated_image.copy(), self.current_gesture,
                    list(self.normalized_hands), list(self.current_finger_coeffs),
                    self.pinch_metric, list(self.current_handedness))

    def close(self):
        if self.landmarker: self.landmarker.close()
