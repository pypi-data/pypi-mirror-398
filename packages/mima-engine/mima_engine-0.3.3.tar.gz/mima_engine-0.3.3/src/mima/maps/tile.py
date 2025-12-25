from ..types.direction import Direction
from ..types.graphic_state import GraphicState
from ..types.terrain import Terrain


class Tile:
    def __init__(self):
        self.basic_tile_id: int = 0
        self.tile_id: int = 0
        self.solid: bool = False
        self.animated: bool = False
        self.pz: float = 0.0
        self.z_height: float = 0.0
        self.terrain: Terrain = Terrain.DEFAULT
        self.facing_direction: Direction = Direction.SOUTH
        self.graphic_state: GraphicState = GraphicState.STANDING
        self.sprite_name: str = ""

    def update(self, elapsed_time: float) -> bool:
        return True
