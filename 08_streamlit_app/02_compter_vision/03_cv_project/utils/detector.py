"""
Detection Module
================
People counting and suspicious action detection using YOLO models.
"""

import cv2
import numpy as np
from typing import Tuple, List, Dict
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class PeopleDetector:
    """Detect and count people in frames"""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize people detector
        
        Args:
            model_path: Path to YOLO model
            confidence_threshold: Detection confidence threshold
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_path)
            except:
                pass
    
    def detect_people(self, frame: np.ndarray) -> Tuple[np.ndarray, int]:
        """Backward compatible detection method"""
        results = self.predict_people(frame)
        annotated_frame = self.annotate_people(frame, results)
        return annotated_frame, len(results)

    def predict_people(self, frame: np.ndarray) -> List:
        """Run inference only"""
        if self.model is None:
            # Fallback for when YOLO is missing (using cascade internally for now)
            # For consistency with the split architecture, we'll just return the cascade rects
            return self._detect_with_cascade_rects(frame)
        
        # Run YOLO detection
        results = self.model(frame, conf=self.confidence_threshold, classes=[0], verbose=False)
        
        # Extract boxes
        boxes = []
        if len(results) > 0:
            for box in results[0].boxes:
                b = box.xyxy[0].cpu().numpy().astype(int)
                boxes.append(b)
        return boxes

    def annotate_people(self, frame: np.ndarray, boxes: List) -> np.ndarray:
        """Draw detections on frame"""
        annotated_frame = frame.copy()
        for b in boxes:
            cv2.rectangle(annotated_frame, (b[0], b[1]), (b[2], b[3]), (0, 255, 0), 2)
        return annotated_frame
    
    def _detect_with_cascade(self, frame: np.ndarray) -> Tuple[np.ndarray, int]:
        """Original fallback method (kept for safe fallback)"""
        rects = self._detect_with_cascade_rects(frame)
        annotated = self.annotate_people(frame, rects)
        return annotated, len(rects)

    def _detect_with_cascade_rects(self, frame: np.ndarray) -> List:
        """Get rects using cascade"""
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        people = cascade.detectMultiScale(gray, 1.1, 4)
        # Convert (x,y,w,h) to (x1,y1,x2,y2)
        rects = []
        for (x, y, w, h) in people:
            rects.append([x, y, x+w, y+h])
        return rects


class ActionDetector:
    """Detect suspicious actions"""
    
    def __init__(self, model_path: str = "yolov8n-pose.pt", confidence_threshold: float = 0.4, sensitivity: str = "Medium"):
        """
        Initialize action detector
        """
        self.confidence_threshold = confidence_threshold
        self.sensitivity = sensitivity
        self.model = None
        self.last_alerts = {} 
        
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO(model_path)
            except:
                pass
    
    def detect_actions(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Dict]]:
        """Backward compatible method"""
        actions, results_obj = self.predict_actions(frame)
        annotated_frame = self.annotate_actions(frame, actions, results_obj)
        return annotated_frame, actions

    def predict_actions(self, frame: np.ndarray) -> Tuple[List[Dict], Any]:
        """Run inference and analysis"""
        if self.model is None:
            return [], None
            
        # Run pose detection
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        actions = []
        
        # Analyze poses
        if len(results) > 0:
            boxes = results[0].boxes
            keypoints = results[0].keypoints
            
            for i in range(len(boxes)):
                # Analyze pose for this person
                action = None
                if keypoints is not None and len(keypoints) > i:
                    action = self._analyze_pose(keypoints[i], i)
                
                if action:
                    # Append box coordinates to action for drawing later
                    box = boxes[i].xyxy[0].cpu().numpy().astype(int)
                    action['box'] = box
                    # Store keypoints index for drawing skeleton if needed
                    # (Simplified: we'll just store the index)
                    action['keypoint_idx'] = i
                    actions.append(action)
                    
        return actions, results

    def annotate_actions(self, frame: np.ndarray, actions: List[Dict], results_obj: Any) -> np.ndarray:
        """Draw actions on frame"""
        annotated_frame = frame.copy()
        
        if self.model is None:
            cv2.putText(annotated_frame, "Model Loading...", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
            return annotated_frame

        # If no actions, return original (maybe draw all skeletons? default behavior was only draw alert skeletons)
        # Original behavior: "COLOR SUSPICIOUS PERSON RED"
        
        for action in actions:
            box = action.get('box')
            if box is None: continue
            
            x1, y1, x2, y2 = box
            color = (0, 0, 255) # Red
            thickness = 3
            
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            
            label = f"⚠️ {action['type'].upper()}!"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Skeleton
            if results_obj and len(results_obj) > 0:
                idx = action.get('keypoint_idx')
                if idx is not None:
                     self._draw_skeleton(annotated_frame, results_obj[0].keypoints[idx], color)
        
        return annotated_frame

    def _draw_skeleton(self, frame, keypoints, color):
        """Draw pose skeleton for a single person"""
        if keypoints is None or len(keypoints.data) == 0:
            return
            
        kp = keypoints.data[0].cpu().numpy()
        
        # Skeleton connections (COCO indices)
        connections = [
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10), # Upper body
            (5, 11), (6, 12), (11, 12),              # Torso
            (11, 13), (13, 15), (12, 14), (14, 16)   # Lower body
        ]
        
        for p1, p2 in connections:
            if kp[p1][2] > 0.5 and kp[p2][2] > 0.5:
                x1, y1 = int(kp[p1][0]), int(kp[p1][1])
                x2, y2 = int(kp[p2][0]), int(kp[p2][1])
                cv2.line(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw joints
        for i in range(5, 17): # Only draw body joints for clarity
            if kp[i][2] > 0.5:
                x, y = int(kp[i][0]), int(kp[i][1])
                cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)
                cv2.circle(frame, (x, y), 2, color, -1)
    
    def _analyze_pose(self, keypoints, person_id: int = 0) -> Dict:
        """
        Analyze pose for suspicious behavior
        
        Args:
            keypoints: Detected keypoints (17 points: nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles)
            person_id: Person identifier
            
        Returns:
            Dictionary with action details or None
        """
        if keypoints is None or len(keypoints.data) == 0:
            return None
        
        try:
            # Extract keypoint coordinates (x, y, confidence)
            kp = keypoints.data[0].cpu().numpy()
            
            # Keypoint indices (COCO format)
            # 0: nose, 1-2: eyes, 3-4: ears
            # 5-6: shoulders, 7-8: elbows, 9-10: wrists
            # 11-12: hips, 13-14: knees, 15-16: ankles
            
            # Check if we have enough confident keypoints
            confident_points = kp[kp[:, 2] > 0.3] # Lowered from 0.5 to 0.3 for better detection
            if len(confident_points) < 5:
                return None
            
            # Extract key body parts
            nose = kp[0]
            left_shoulder = kp[5]
            right_shoulder = kp[6]
            left_elbow = kp[7]
            right_elbow = kp[8]
            left_wrist = kp[9]
            right_wrist = kp[10]
            left_hip = kp[11]
            right_hip = kp[12]
            left_knee = kp[13]
            right_knee = kp[14]
            left_ankle = kp[15]
            right_ankle = kp[16]
            
            # Calculate body metrics
            shoulder_mid_y = (left_shoulder[1] + right_shoulder[1]) / 2
            hip_mid_y = (left_hip[1] + right_hip[1]) / 2
            body_height = abs(hip_mid_y - shoulder_mid_y)
            
            # Sensitivity multipliers
            sens_map = {"Low": 1.2, "Medium": 1.0, "High": 0.8}
            sens_val = sens_map.get(self.sensitivity, 1.0)
            
            # SUSPICIOUS ACTION 1: Person Falling
            if nose[2] > 0.3 and left_hip[2] > 0.3 and right_hip[2] > 0.3:
                # If head is significantly below shoulders or near hips
                if nose[1] > shoulder_mid_y + body_height * 0.2 * sens_val:
                    return {
                        'type': 'falling',
                        'severity': 'high',
                        'description': 'Fall detected or person lying down',
                        'person_id': person_id
                    }
            
            # SUSPICIOUS ACTION 2: Hands Up (Robbery/Surrender)
            left_hand_raised = False
            right_hand_raised = False
            
            # Check left hand (Wrist above shoulder or nose)
            if left_wrist[2] > 0.3:
                if left_wrist[1] < left_shoulder[1] or (nose[2] > 0.3 and left_wrist[1] < nose[1]):
                    left_hand_raised = True
            
            # Check right hand  
            if right_wrist[2] > 0.3:
                if right_wrist[1] < right_shoulder[1] or (nose[2] > 0.3 and right_wrist[1] < nose[1]):
                    right_hand_raised = True
            
            if left_hand_raised and right_hand_raised:
                return {
                    'type': 'hands_up',
                    'severity': 'high',
                    'description': 'Hands up detected (possible threat)',
                    'person_id': person_id
                }
            elif (left_hand_raised or right_hand_raised):
                # Trigger on Medium and High sensitivity
                if self.sensitivity in ["Medium", "High"]:
                    return {
                        'type': 'hand_raised',
                        'severity': 'medium',
                        'description': 'Suspicious hand movement detected',
                        'person_id': person_id
                    }

            
            # SUSPICIOUS ACTION 3: Crouching/Hiding
            if (left_knee[2] > 0.5 and right_knee[2] > 0.5 and 
                nose[2] > 0.5):
                knee_mid_y = (left_knee[1] + right_knee[1]) / 2
                # Head close to knees (crouching)
                if abs(nose[1] - knee_mid_y) < body_height * 0.8:
                    return {
                        'type': 'crouching',
                        'severity': 'medium',
                        'description': 'Person crouching or hiding',
                        'person_id': person_id
                    }
            
            # SUSPICIOUS ACTION 4: Fighting Pose (Aggressive stance)
            if (left_elbow[2] > 0.4 and right_elbow[2] > 0.4 and
                left_wrist[2] > 0.4 and right_wrist[2] > 0.4):
                
                # Wrists raised near or above shoulder level
                left_raised = left_wrist[1] < left_shoulder[1] + body_height * 0.1
                right_raised = right_wrist[1] < right_shoulder[1] + body_height * 0.1
                
                # Wrists extended away from body (punching/guarding)
                shoulder_width = abs(left_shoulder[0] - right_shoulder[0])
                left_ext = abs(left_wrist[0] - left_shoulder[0]) > shoulder_width * 0.5
                right_ext = abs(right_wrist[0] - right_shoulder[0]) > shoulder_width * 0.5
                
                if (left_raised and left_ext) or (right_raised and right_ext):
                    return {
                        'type': 'aggressive_stance',
                        'severity': 'high',
                        'description': 'Aggressive stance (arm extended/raised)',
                        'person_id': person_id
                    }
            
            # SUSPICIOUS ACTION 5: Running (Fast movement - requires frame comparison)
            # This would need temporal tracking, placeholder for now
            
            return None
            
        except Exception as e:
            # Silently handle errors in pose analysis
            return None
