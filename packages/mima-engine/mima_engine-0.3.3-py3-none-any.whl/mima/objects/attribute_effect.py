from .attributes import Attributes


class Effect(Attributes):
    def __init__(self):
        super().__init__()

        self.effect_id: str = ""
        self.duration: float = 0.0
        self.redundant: bool = False
        self.health_cost: float = 0.0
        self.magic_cost: float = 0.0
        self.stamina_cost: float = 0.0

    def update(self, elapsed_time: float):
        self.duration -= self.elapsed_time
        if self.duration < 0.0:
            self.redundant = True

    @staticmethod
    def from_dict(data):
        attr = Effect()
        for key, val in data.items():
            setattr(attr, key, val)

        return attr
