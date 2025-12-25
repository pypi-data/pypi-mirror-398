from enum import Enum


class Command:
    """A script that can be used to interact with the game engine.

    Args:
        scopes: The scopes this command should be added to.

    Attributes:
        started: Indicates if this command has started.
        completed: Indicates if this command has completed.
        interruptible: Indicates if this command can be finished before it has
            completed (it still can be forced to complete, regardless of this
            flag).
        scopes: A list containing different command scopes. This is to be
            interpreted by the game engine, but can, e.g., be used to
            differentiate between different players in a split-screen
            multiplayer session.

    """

    def __init__(self, scopes: list[int] | None = None) -> None:
        self.started: bool = False
        self.completed: bool = False
        self.interruptible: bool = False
        self.scopes: list[int] = scopes if scopes else [0]

    def start(self) -> None:
        """Start this command in the next frame."""
        return

    def _start(self) -> None:
        """Prepare for start and start this command (internal function)."""
        self.started = True
        self.start()

    def update(self, elapsed_time: float) -> bool:
        """Update this command."""
        return False

    def finalize(self) -> None:
        """Finalize the operation of this command and clean-up."""
        pass

    def set_scopes(self, scopes: list[int]) -> None:
        """Set or override the scopes variable of this command."""
        self.scopes = scopes


class CompleteWhen(Enum):
    ALL_COMPLETED = 0
    ANY_COMPLETED = 1
    FIRST_COMPLETED = 2


class CommandParallel(Command):
    """A script that executes multiple commands in parallel.

    This command completes based on different termination conditions. It either
    completes after all subcommands are completed, after any subcommand is
    completed, or if the first command in the list is completed.

    """

    def __init__(
        self,
        cmds: list[Command],
        completed_when: CompleteWhen = CompleteWhen.ALL_COMPLETED,
        scopes: list[int] | None = None,
    ) -> None:
        super().__init__(scopes)

        self._cmds: list[Command] = cmds
        self._completed_when: CompleteWhen = completed_when

    def start(self) -> None:
        for cmd in self._cmds:
            cmd.start()

    def update(self, elapsed_time: float) -> bool:
        for cmd in self._cmds:
            cmd.update(elapsed_time)

        if self._completed_when == CompleteWhen.ALL_COMPLETED:
            self.completed = True
            for cmd in self._cmds:
                self.completed = self.completed and cmd.completed
        elif self._completed_when == CompleteWhen.ANY_COMPLETED:
            self.completed = False
            for cmd in self._cmds:
                self.completed = self.completed or cmd.completed
        elif self._completed_when == CompleteWhen.FIRST_COMPLETED:
            self.completed = self._cmds[0].completed
        else:
            msg = f"Unknown termination condition: {self._completed_when}"
            raise ValueError(msg)

        return self.completed

    def set_scopes(self, scopes: list[int]) -> None:
        self.scopes = scopes
        for cmd in self._cmds:
            cmd.set_scopes(scopes)


class ScriptProcessor:
    def __init__(self) -> None:
        self._commands: dict[int, list[Command]] = {}
        self._script_active: dict[int, bool] = {}

    def add_command(self, cmd: Command, scopes: list[int] | None = None) -> None:
        if scopes:
            cmd.set_scopes(scopes)

        for scope in cmd.scopes:
            self._commands.setdefault(scope, []).append(cmd)

    def process_command(self, elapsed_time: float) -> bool:
        for scope in self._commands:
            if not self._commands[scope]:
                self._script_active[scope] = False
                continue

            self._script_active[scope] = True
            if not self._commands[scope][0].completed:
                if not self._commands[scope][0].started:
                    self._commands[scope][0]._start()
                else:
                    self._commands[scope][0].update(elapsed_time)
            else:
                self._commands[scope][0].finalize()
                self._commands[scope].pop()
                self._script_active[scope] = False

        return any(list(self._script_active.values()))

    def complete_command(self, scope: int, force: bool = False) -> bool:
        if scope not in self._commands or not self._commands[scope]:
            return True

        if self._commands[scope][0].interruptible or force:
            self._commands[scope][0].completed = True
            return True
        return False
