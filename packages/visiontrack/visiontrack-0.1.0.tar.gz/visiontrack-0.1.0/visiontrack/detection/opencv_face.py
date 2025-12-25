import cv2
from visiontrack.types import Face, BoundingBox
from visiontrack.detection.base import FaceDetector

class OpenCVFaceDetector(FaceDetector):
    def __init__(self):
        self.detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, 1.3, 5)

        results = []
        for (x, y, w, h) in faces:
            bbox = BoundingBox(x, y, x + w, y + h)
            results.append(Face(bbox=bbox))

        return results
