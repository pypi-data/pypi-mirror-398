from abc import ABC, abstractmethod

class FaceRecognizer(ABC):
    @abstractmethod
    def embed(self, face_image):
        pass

    @abstractmethod
    def compare(self, emb1, emb2) -> float:
        pass
