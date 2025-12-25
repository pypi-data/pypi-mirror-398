from ..command import Command


class CommandQuitGame(Command):
    def start(self):
        self.engine.game_state.save_to_disk(autosave=True)
        self.engine.backend.terminate = True
        self.completed = True
