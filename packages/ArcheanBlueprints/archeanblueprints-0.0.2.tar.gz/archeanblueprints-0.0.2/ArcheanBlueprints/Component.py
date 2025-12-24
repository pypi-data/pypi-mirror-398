

class Component:
    def __init__(self):
        self.pos_x = None
        self.pos_y = None
        self.pos_z = None

        self.orientation_w = None
        self.orientation_x = None
        self.orientation_y = None
        self.orientation_z = None

        self.occupancies = None

        self.colors = None

        self.module = None
        self.type = None
        self.alias = None
        self.elements = None
        self.data = None

    def from_dict(self, dic: dict):
        
        self.alias = dic["alias"]
        self.colors = dic["colors"]
        self.data = dic["data"]
        self.type = dic["type"]

        self.occupancies = dic["occupancies"]

        position = dic["position"]
        self.pos_x = position["x"]
        self.pos_y = position["y"]
        self.pos_z = position["z"]

        orientation = dic["orientation"]
        self.orientation_w = orientation["w"]
        self.orientation_x = orientation["x"]
        self.orientation_y = orientation["y"]
        self.orientation_z = orientation["z"]    

    def __str__(self) -> str:
        return f"alias:'{self.alias}', colors:{self.colors}, data:{self.data}, component_type:{self.type}, occupancies:{self.occupancies}; pos_x:{self.pos_x}, pos_y:{self.pos_y}, pos_z:{self.pos_z}; orient_w:{self.orientation_w}, orient_x:{self.orientation_x}, orient_y:{self.orientation_y}, orient_z{self.orientation_z}"
        