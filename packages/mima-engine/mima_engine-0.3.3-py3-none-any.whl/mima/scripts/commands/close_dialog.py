from ..command import Command


class CommandCloseDialog(Command):
    def start(self):
        for player in self.players:
            self.engine.trigger_dialog(False, player)
        self.engine.exit_dialog_active = False
        self.completed = True
