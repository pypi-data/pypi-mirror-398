class FacePipeline:
    def __init__(self, detector, recognizer=None, tracker=None):
        self.detector = detector
        self.recognizer = recognizer
        self.tracker = tracker

    def process(self, frame):
        faces = self.detector.detect(frame)

        if self.recognizer:
            for face in faces:
                x1, y1, x2, y2 = face.bbox.__dict__.values()
                crop = frame[y1:y2, x1:x2]
                face.embedding = self.recognizer.embed(crop)

        if self.tracker:
            faces = self.tracker.update(faces)

        return faces
