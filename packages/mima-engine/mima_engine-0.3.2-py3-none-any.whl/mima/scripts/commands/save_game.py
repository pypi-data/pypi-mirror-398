from ...scripts.command import Command


class CommandSaveGame(Command):
    def start(self):
        # print(self.engine.game_state._state["player"])
        # print(self.engine.items)
        for quest in self.engine.quests:
            quest.save_state()
        self.engine.game_state.save_to_disk()
        self.completed = True
        print(f"Saved the game to {self.engine.game_state.state_name}")

        # print(self.engine.game_state._state["player"])
