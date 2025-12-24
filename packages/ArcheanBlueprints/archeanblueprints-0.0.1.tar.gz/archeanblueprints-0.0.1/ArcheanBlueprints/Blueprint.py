import json
from ArcheanBlueprints.Block import Block
from ArcheanBlueprints.Component import Component
from ArcheanBlueprints.Frame import Frame

class Blueprint:
    def __init__(self, file_path: str, auto_load_blueprint: bool = True, auto_extract_data: bool = True):
        
        self.raw_data = None
        self.components: list[Component] = []
        self.blocks: list[Block] = []
        self.frames = []

        if file_path:
            self.file_path = file_path
        if auto_load_blueprint and file_path:
            self.load_raw_blueprint()
            if auto_extract_data:
                self.extract_all_from_raw_data()

    def load_raw_blueprint(self):
        data = None
        with open(self.file_path, "r") as file:
            data = json.load(file)
        self.raw_data = data
    
    def extract_all_from_raw_data(self):
        self.extract_blocks_from_raw_data()
        self.extract_components_from_raw_data()
        self.extract_frames_from_raw_data()

    def extract_blocks_from_raw_data(self):
        if self.raw_data == None:
            return
        
        for i in self.raw_data["data"]["blocks"]:
            block = Block()
            block.from_dict(i)
            self.blocks.append(block)

    def extract_components_from_raw_data(self):
        if self.raw_data == None:
            return
        
        for i in self.raw_data["data"]["components"]:
            component = Component()
            component.from_dict(i)
            self.components.append(component)

    def extract_frames_from_raw_data(self):
        if self.raw_data == None:
            return
        
        for i in self.raw_data["data"]["frames"]:
            frame = Frame()
            frame.from_dict(i)
            self.frames.append(frame)
