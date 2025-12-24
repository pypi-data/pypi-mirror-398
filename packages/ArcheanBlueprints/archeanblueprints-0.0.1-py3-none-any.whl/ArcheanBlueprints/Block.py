from ArcheanBlueprints.Enums import BlockType

class Block:
    def __init__(self, pos_x: int|None = None, pos_y: int|None = None, pos_z: int|None = None, size_x: int|None = None, size_y: int|None = None, size_z: int|None = None, block_type: BlockType|None = None):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos_z = pos_z

        self.size_x = size_x
        self.size_y = size_y
        self.size_z = size_z

        self.block_type = block_type

    def from_dict(self, dictionary: dict):
        self.pos_x = dictionary["pos_x"]
        self.pos_y = dictionary["pos_y"]
        self.pos_z = dictionary["pos_z"]

        self.size_x = dictionary["size_x"]
        self.size_y = dictionary["size_y"]
        self.size_z = dictionary["size_z"]

        self.block_type = BlockType.Cube # Temporary for now

    def __str__(self) -> str:
        return f"pos_x.{self.pos_x}, pos_y:{self.pos_y}, pos_z:{self.pos_z}; size_x:{self.size_x}, size_y:{self.size_y}, size_z:{self.size_z}; block_type:{self.block_type}"

