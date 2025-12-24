

class Frame:
    def __init__(self):
        self.beams: list[bool] = []

        self.pos_x = None
        self.pos_y = None
        self.pos_z = None

    def from_dict(self, dictionary: dict):
        self.beams = dictionary["beams"]

        self.pos_x = dictionary["frame_x"]
        self.pos_y = dictionary["frame_y"]
        self.pos_z = dictionary["frame_z"]

    def __str__(self) -> str:
        return f"beams:{self.beams}; pos_x:{self.pos_x}, pos_y:{self.pos_y}, pos_z:{self.pos_z}"