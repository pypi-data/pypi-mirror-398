import cv2
from visiontrack.detection.opencv_face import OpenCVFaceDetector
from visiontrack.pipeline.face_pipeline import FacePipeline

cap = cv2.VideoCapture(0)

pipeline = FacePipeline(detector=OpenCVFaceDetector())

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = pipeline.process(frame)

    for face in faces:
        b = face.bbox
        cv2.rectangle(frame, (b.x1, b.y1), (b.x2, b.y2), (0,255,0), 2)

    cv2.imshow("VisionTrack", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
