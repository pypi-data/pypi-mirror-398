from abc import ABC, abstractmethod

class Tracker(ABC):
    @abstractmethod
    def update(self, detections):
        pass
