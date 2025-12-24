from ArcheanBlueprints.Component import Component

class PipeSegment:
    def __init__(self):
        
        self.box: bool|None = None
        self.dir: int|None = None
        self.flexible: bool|None = None
        self.length: float|None = None

        self.x: float|None = None
        self.y: float|None = None
        self.z: float|None = None

        self.r: int|None = None
        self.g: int|None = None
        self.b: int|None = None
        self.a: int|None = None
        self.glossy: bool|None = None
        self.metal: bool|None = None
        self.chrome: bool|None = None
        self.striped: bool|None = None

        self.rounded_caps: bool|None = None

    def from_dict(self, dic:dict):
        position = dic["start"]
        self.x = position["x"]
        self.y = position["y"]
        self.z = position["z"]

        self.r = dic["r"]
        self.g = dic["g"]
        self.b = dic["b"]
        self.a = dic["a"]

        self.glossy = dic["glossy"]
        self.metal = dic["metal"]
        self.chrome = dic["chrome"]
        self.striped = dic["striped"]
        self.rounded_caps = dic["rounded_caps"]

        self.box = dic["box"]
        self.dir = dic["dir"]
        self.flexible = dic["flexible"]
        self.lenght = dic["flexible"]

    def __str__(self) -> str:
        return f"box:{self.box}, dir:{self.dir}, flexible:{self.flexible}, length:{self.length}; x:{self.x}, y:{self.y}, z:{self.z}; r:{self.r}, g:{self.g}, b:{self.b}, a:{self.a}; glossy:{self.glossy}, metal:{self.metal}, chrome:{self.chrome}, striped:{self.striped}, rounded_caps:{self.rounded_caps}"

class Pipe:
    def __init__(self):
        self.component_a: Component|None = None
        self.component_b: Component|None = None

        self.port_a: str|None = None
        self.port_b: str|None = None

        self.radius: float|None = None
        self.type: str|None = None

        self.segments: list[PipeSegment] = []

    def from_dict(self, dic:dict):
        self.component_a = dic["a_component"]
        self.component_b = dic["b_component"]

        self.port_a = dic["a_port"]
        self.port_b = dic["b_port"]

        self.radius = dic["radius"]
        self.type = dic["type"]

        for i in dic["segments"]:
            segment = PipeSegment()
            segment.from_dict(i)
            self.segments.append(segment)

    def __str__(self) -> str:
        return f"a_component:{self.component_a}, b_component:{self.component_b}; a_port:'{self.port_a}', b_port:'{self.port_b}'; radius:{self.radius}, pipe_type:{self.type}; segments:[{', '.join(str(s) for s in self.segments)}]"
