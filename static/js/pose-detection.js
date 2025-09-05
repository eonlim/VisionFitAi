// VisionFit AI - Pose Detection Utilities
// Main functionality moved to exercise_analysis.html template

// Utility functions for pose detection
class PoseUtils {
    static calculateAngle(a, b, c) {
        const radians = Math.atan2(c[1] - b[1], c[0] - b[0]) - Math.atan2(a[1] - b[1], a[0] - b[0]);
        let angle = Math.abs(radians * 180.0 / Math.PI);
        if (angle > 180.0) {
            angle = 360 - angle;
        }
        return angle;
    }

    static getDistance(point1, point2) {
        const dx = point1.x - point2.x;
        const dy = point1.y - point2.y;
        return Math.sqrt(dx * dx + dy * dy);
    }

    static isLandmarkVisible(landmark, threshold = 0.5) {
        return landmark && landmark.visibility > threshold;
    }
}

// Export for global use
window.PoseUtils = PoseUtils;

console.log('Pose detection utilities loaded');