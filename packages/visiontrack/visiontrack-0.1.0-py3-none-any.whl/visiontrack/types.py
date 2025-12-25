from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

@dataclass
class Face:
    bbox: BoundingBox
    score: float = 1.0
    embedding: Optional[list] = None
