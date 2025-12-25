from abc import ABC, abstractmethod
from typing import List
from visiontrack.types import Face

class FaceDetector(ABC):
    @abstractmethod
    def detect(self, image) -> List[Face]:
        pass
