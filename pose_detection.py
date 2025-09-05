
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

class PoseAnalyzer:
    """Analyze poses for different exercises and provide form feedback"""

    def __init__(self):
        self.exercise_counters = {
            'pushup': PushupCounter(),
            'squat': SquatCounter(),
            'jumping_jack': JumpingJackCounter()
        }

    def analyze_pose(self, landmarks: List[Dict], exercise_type: str) -> Dict:
        """Analyze pose and return form score and feedback"""
        try:
            if exercise_type not in self.exercise_counters:
                return {"error": "Unsupported exercise type"}

            if not landmarks or len(landmarks) < 33:
                return {"error": "Insufficient landmarks detected"}

            counter = self.exercise_counters[exercise_type]
            result = counter.analyze(landmarks)
            
            # Ensure consistent return format
            return {
                "reps": result.get("reps", 0),
                "form_score": result.get("form_score", 0),
                "feedback": result.get("feedback", ["No feedback available"]),
                "success": True
            }

        except Exception as e:
            logging.error(f"Error in pose analysis: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "reps": 0,
                "form_score": 0,
                "feedback": ["Analysis error occurred"],
                "success": False
            }

class PushupCounter:
    """Pushup form analysis and counting"""

    def __init__(self):
        self.state = "up"  # up, down
        self.rep_count = 0
        self.last_angle = 180

    def analyze(self, landmarks: List[Dict]) -> Dict:
        """Analyze pushup form and count reps"""
        try:
            # Get key points for pushup analysis
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_elbow = landmarks[13]
            right_elbow = landmarks[14]
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            # Calculate arm angles
            left_arm_angle = self._calculate_angle(
                [left_shoulder['x'], left_shoulder['y']],
                [left_elbow['x'], left_elbow['y']],
                [left_wrist['x'], left_wrist['y']]
            )

            right_arm_angle = self._calculate_angle(
                [right_shoulder['x'], right_shoulder['y']],
                [right_elbow['x'], right_elbow['y']],
                [right_wrist['x'], right_wrist['y']]
            )

            avg_arm_angle = (left_arm_angle + right_arm_angle) / 2

            # Calculate body alignment
            body_alignment_score = self._calculate_body_alignment(
                left_shoulder, right_shoulder, left_hip, right_hip
            )

            # Count reps based on arm angle with stricter thresholds
            if self.state == "up" and avg_arm_angle < 90:
                self.state = "down"
            elif self.state == "down" and avg_arm_angle > 160:
                self.state = "up"
                self.rep_count += 1

            # Calculate form score (0-100)
            form_score = self._calculate_pushup_form_score(avg_arm_angle, body_alignment_score)

            # Generate feedback
            feedback = self._generate_pushup_feedback(avg_arm_angle, body_alignment_score)

            return {
                "reps": self.rep_count,
                "form_score": round(form_score, 1),
                "feedback": feedback,
                "arm_angle": round(avg_arm_angle, 1),
                "body_alignment": round(body_alignment_score, 1),
                "state": self.state
            }

        except Exception as e:
            logging.error(f"Error in pushup analysis: {e}")
            return {"error": "Pushup analysis failed"}

    def _calculate_angle(self, a: List[float], b: List[float], c: List[float]) -> float:
        """Calculate angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def _calculate_body_alignment(self, left_shoulder: Dict, right_shoulder: Dict,
                                left_hip: Dict, right_hip: Dict) -> float:
        """Calculate body alignment score (higher is better)"""
        # Check if shoulders and hips are aligned (straight line)
        shoulder_center = [(left_shoulder['x'] + right_shoulder['x']) / 2,
                          (left_shoulder['y'] + right_shoulder['y']) / 2]
        hip_center = [(left_hip['x'] + right_hip['x']) / 2,
                     (left_hip['y'] + right_hip['y']) / 2]

        # Calculate deviation from straight line
        vertical_deviation = abs(shoulder_center[1] - hip_center[1])

        # Convert to score (lower deviation = higher score)
        alignment_score = max(0, 100 - (vertical_deviation * 1000))
        return min(100, alignment_score)

    def _calculate_pushup_form_score(self, arm_angle: float, body_alignment: float) -> float:
        """Calculate overall form score for pushup"""
        # Ideal arm angle range: 60-90 degrees at bottom, 160-180 at top
        if 60 <= arm_angle <= 90 or 160 <= arm_angle <= 180:
            angle_score = 100
        elif 90 < arm_angle < 160:
            # Transition zone - moderate score
            angle_score = 70
        else:
            angle_score = max(0, 100 - abs(arm_angle - 90) * 2)

        # Combine scores
        form_score = (angle_score * 0.7) + (body_alignment * 0.3)
        return min(100, max(0, form_score))

    def _generate_pushup_feedback(self, arm_angle: float, body_alignment: float) -> List[str]:
        """Generate feedback for pushup form"""
        feedback = []

        if arm_angle < 60:
            feedback.append("Don't go too low - protect your shoulders")
        elif arm_angle < 90 and self.state == "down":
            feedback.append("Good depth! Now push up")
        elif arm_angle > 120 and arm_angle < 160:
            feedback.append("Push all the way up")
        elif arm_angle >= 160:
            feedback.append("Great form!")

        if body_alignment < 70:
            feedback.append("Keep your body straight - avoid sagging")

        if not feedback:
            feedback.append("Excellent form!")

        return feedback


class SquatCounter:
    """Squat form analysis and counting"""

    def __init__(self):
        self.state = "up"  # up, down
        self.rep_count = 0

    def analyze(self, landmarks: List[Dict]) -> Dict:
        """Analyze squat form and count reps"""
        try:
            # Get key points for squat analysis
            left_hip = landmarks[23]
            right_hip = landmarks[24]
            left_knee = landmarks[25]
            right_knee = landmarks[26]
            left_ankle = landmarks[27]
            right_ankle = landmarks[28]

            # Calculate knee angles
            left_knee_angle = self._calculate_angle(
                [left_hip['x'], left_hip['y']],
                [left_knee['x'], left_knee['y']],
                [left_ankle['x'], left_ankle['y']]
            )

            right_knee_angle = self._calculate_angle(
                [right_hip['x'], right_hip['y']],
                [right_knee['x'], right_knee['y']],
                [right_ankle['x'], right_ankle['y']]
            )

            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2

            # Count reps based on knee angle with better thresholds
            if self.state == "up" and avg_knee_angle < 120:
                self.state = "down"
            elif self.state == "down" and avg_knee_angle > 160:
                self.state = "up"
                self.rep_count += 1

            # Calculate form score
            form_score = self._calculate_squat_form_score(avg_knee_angle)

            # Generate feedback
            feedback = self._generate_squat_feedback(avg_knee_angle)

            return {
                "reps": self.rep_count,
                "form_score": round(form_score, 1),
                "feedback": feedback,
                "knee_angle": round(avg_knee_angle, 1),
                "state": self.state
            }

        except Exception as e:
            logging.error(f"Error in squat analysis: {e}")
            return {"error": "Squat analysis failed"}

    def _calculate_angle(self, a: List[float], b: List[float], c: List[float]) -> float:
        """Calculate angle between three points"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def _calculate_squat_form_score(self, knee_angle: float) -> float:
        """Calculate overall form score for squat"""
        # Ideal knee angle range: 80-120 degrees at bottom, 160-180 at top
        if 80 <= knee_angle <= 120 or 160 <= knee_angle <= 180:
            return 100
        elif 120 < knee_angle < 160:
            # Transition zone
            return 70
        else:
            return max(0, 100 - abs(knee_angle - 100) * 1.5)

    def _generate_squat_feedback(self, knee_angle: float) -> List[str]:
        """Generate feedback for squat form"""
        feedback = []

        if knee_angle < 80:
            feedback.append("Don't squat too deep")
        elif knee_angle <= 120 and self.state == "down":
            feedback.append("Perfect depth! Now stand up")
        elif knee_angle > 130 and knee_angle < 160:
            feedback.append("Stand up completely")
        elif knee_angle >= 160:
            feedback.append("Great squat!")

        if not feedback:
            feedback.append("Excellent form!")

        return feedback


class JumpingJackCounter:
    """Jumping jack form analysis and counting"""

    def __init__(self):
        self.state = "closed"  # closed, open
        self.rep_count = 0

    def analyze(self, landmarks: List[Dict]) -> Dict:
        """Analyze jumping jack form and count reps"""
        try:
            # Get key points
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            left_ankle = landmarks[27]
            right_ankle = landmarks[28]
            nose = landmarks[0]

            # Calculate spreads
            arm_spread = abs(right_wrist['x'] - left_wrist['x'])
            leg_spread = abs(right_ankle['x'] - left_ankle['x'])

            # Normalize by body height
            body_height = abs(nose['y'] - min(left_ankle['y'], right_ankle['y']))
            arm_ratio = arm_spread / body_height if body_height > 0 else 0
            leg_ratio = leg_spread / body_height if body_height > 0 else 0

            # Determine position
            is_open = arm_ratio > 0.3 and leg_ratio > 0.2

            # Count reps
            if self.state == "closed" and is_open:
                self.state = "open"
            elif self.state == "open" and not is_open:
                self.state = "closed"
                self.rep_count += 1

            # Calculate form score
            form_score = self._calculate_jumping_jack_form_score(arm_ratio, leg_ratio)

            # Generate feedback
            feedback = self._generate_jumping_jack_feedback(arm_ratio, leg_ratio)

            return {
                "reps": self.rep_count,
                "form_score": round(form_score, 1),
                "feedback": feedback,
                "state": self.state,
                "arm_ratio": round(arm_ratio, 2),
                "leg_ratio": round(leg_ratio, 2)
            }

        except Exception as e:
            logging.error(f"Error in jumping jack analysis: {e}")
            return {"error": "Jumping jack analysis failed"}

    def _calculate_jumping_jack_form_score(self, arm_ratio: float, leg_ratio: float) -> float:
        """Calculate overall form score for jumping jack"""
        # Good coordination when arms and legs move together
        coordination_diff = abs(arm_ratio - leg_ratio)
        coordination_score = max(0, 100 - (coordination_diff * 200))
        
        # Good range of motion
        range_score = min(100, (arm_ratio + leg_ratio) * 100)
        
        return (coordination_score * 0.6) + (range_score * 0.4)

    def _generate_jumping_jack_feedback(self, arm_ratio: float, leg_ratio: float) -> List[str]:
        """Generate feedback for jumping jack form"""
        feedback = []

        if arm_ratio < 0.2:
            feedback.append("Raise your arms higher")
        if leg_ratio < 0.15:
            feedback.append("Jump with wider legs")
        
        coordination_diff = abs(arm_ratio - leg_ratio)
        if coordination_diff > 0.1:
            feedback.append("Coordinate arms and legs together")
        
        if not feedback:
            feedback.append("Perfect jumping jacks!")

        return feedback
