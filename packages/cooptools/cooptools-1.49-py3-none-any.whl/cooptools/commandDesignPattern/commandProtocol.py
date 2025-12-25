from typing import Protocol, List, TypeVar
from dataclasses import dataclass
from cooptools.commandDesignPattern.exceptions import ResolveBatchException

T = TypeVar("T")

class CommandProtocol(Protocol):
    def execute(self, state: T) -> T:
        ...

@dataclass
class CommandBatch(CommandProtocol):
    commands: List[CommandProtocol]

    def execute(self, state: T) -> T:


        try:
            new = state
            for command in self.commands:
                new = command.execute(new)
                if new is None:
                    raise Exception("The command.execute() operation returned a None value")
            return new
        except Exception as e:
            # raise the exception on the command that failed
            raise ResolveBatchException(batch=self, inner=e)

