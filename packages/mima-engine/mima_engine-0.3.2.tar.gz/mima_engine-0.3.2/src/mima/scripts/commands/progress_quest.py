from ..command import Command


class CommandProgressQuest(Command):
    def __init__(self, quest_name: str, new_state: int):
        super().__init__()
        self._quest_name: str = quest_name
        self._new_state: int = new_state

    def start(self):
        self.engine.progress_quest(self._quest_name, self._new_state)
        self.completed = True
