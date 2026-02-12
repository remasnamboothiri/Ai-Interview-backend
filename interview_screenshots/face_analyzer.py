import cv2
import mediapipe as mp
import numpy as np
from PIL import Image
import io

class FaceAnalyzer:
    """Analyzes screenshots for proctoring violations using MediaPipe"""
    
    def __init__(self):
        # Initialize MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 1 = full range detection (better for interviews)
            min_detection_confidence=0.5  # 50% confidence threshold
        )
    
    def analyze_image(self, image_file):
        """
        Analyze an image for proctoring issues
        
        Args:
            image_file: Django UploadedFile object or file path
            
        Returns:
            dict with analysis results
        """
        try:
            # Convert uploaded file to OpenCV format
            image = self._load_image(image_file)
            
            # Convert BGR to RGB (MediaPipe uses RGB)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Run face detection
            results = self.face_detection.process(image_rgb)
            
            # Count faces
            face_count = 0
            if results.detections:
                face_count = len(results.detections)
            
            # Determine issue type
            issue_type = None
            multiple_people = False
            confidence_score = 0.0
            
            if face_count == 0:
                issue_type = 'no_face'
                confidence_score = 0.95
            elif face_count > 1:
                issue_type = 'multiple_people'
                multiple_people = True
                confidence_score = 0.90
            else:
                # Exactly 1 face - all good!
                confidence_score = results.detections[0].score[0]
            
            return {
                'face_count': face_count,
                'multiple_people_detected': multiple_people,
                'issue_type': issue_type,
                'confidence_score': float(confidence_score),
                'success': True
            }
            
        except Exception as e:
            return {
                'face_count': 0,
                'multiple_people_detected': False,
                'issue_type': None,
                'confidence_score': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _load_image(self, image_file):
        """Convert Django uploaded file to OpenCV image"""
        if isinstance(image_file, str):
            # If it's a file path
            return cv2.imread(image_file)
        else:
            # If it's an uploaded file object
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode to OpenCV image
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'face_detection'):
            self.face_detection.close()
