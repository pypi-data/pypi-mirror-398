from enum import Enum

class BlockType(Enum):
    Cube = 1
    Slope = 2
    Corner = 3
    Pyramid = 4
    InvCorner = 5

    def __str__(self):
        return self.name