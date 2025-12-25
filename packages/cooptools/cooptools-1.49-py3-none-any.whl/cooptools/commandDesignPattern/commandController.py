from dataclasses import dataclass, field
from cooptools.commandDesignPattern.commandProtocol import CommandProtocol
from cooptools.commandDesignPattern.exceptions import ResolveStateException
from typing import List, Tuple, TypeVar, Dict, Protocol, Callable
import threading
import copy
import logging
import pprint

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CommandStore(Protocol):
    def __init__(self, reset_state: bool = False):
        if reset_state:
            self.clear_all_state()

    def add_command(self, command: CommandProtocol, cursor: int) -> List[CommandProtocol]:
        raise NotImplementedError()

    def remove_commands(self, start_cursor: int) -> List[CommandProtocol]:
        raise NotImplementedError()

    def get_commands(self, start_cursor: int = None, end_cursor: int = None) -> List[CommandProtocol]:
        raise NotImplementedError()

    def add_cached(self, state: T, cursor: int) -> Dict[int, T]:
        raise NotImplementedError()

    def remove_cached_at_cursor(self, cursor: int) -> Dict[int, T]:
        raise NotImplementedError()

    def get_cached(self) -> Dict[int, T] :
        raise NotImplementedError()

    def _get_last_cached(self, max_idx = None) -> Tuple[T, int]:
        raise NotImplementedError()

    def add_update_cached(self, state: T, cursor: int):
        self.remove_cached_at_cursor(cursor)
        self.add_cached(state, cursor)

    def last_cached(self, max_idx = None) -> Tuple[T, int]:
        try:
            return self._get_last_cached(max_idx)
        except:
            cached = self.get_cached()
            max_cached_idx = max(x for x in cached.keys() if max_idx is None or x <= max_idx)
            last_cached_state = cached[max_cached_idx]
            return last_cached_state, max_cached_idx

    def clear_cache(self):
        cached = self.get_cached()
        for cursor in cached.keys():
            self.remove_cached_at_cursor(cursor)

    def clear_commands(self):
        self.remove_commands(0)

    def clear_all_state(self):
        self.clear_commands()
        self.clear_cache()


@dataclass
class InMemoryCommandStore(CommandStore):
    command_stack: List[CommandProtocol] = field(default_factory=list, init=False)
    _cached_states: Dict[int, T] = field(default_factory=dict, init=False)

    def add_command(self, command: CommandProtocol, cursor: int) -> List[CommandProtocol]:
        self.command_stack.append(command)
        return self.command_stack

    def remove_commands(self, start_cursor: int) -> List[CommandProtocol]:
        self.command_stack = self.command_stack[:start_cursor]
        return self.command_stack

    def get_commands(self, start_cursor: int = None, end_cursor: int = None) -> List[CommandProtocol]:
        return self.command_stack[start_cursor: end_cursor]

    def add_cached(self, state: T, cursor: int) -> Dict[int, T]:
        self._cached_states[cursor] = state
        return self._cached_states

    def remove_cached_at_cursor(self, cursor: int) -> Dict[int, T]:
        del self._cached_states[cursor]
        return self._cached_states

    def get_cached(self) -> Dict[int, T]:
        return self._cached_states

    def _get_last_cached(self, max_idx = None) -> Tuple[T, int]:
        if len(self._cached_states.keys()) == 0:
            return None, None

        approp_max = max(x for x in self._cached_states.keys() if max_idx is None or x < max_idx)
        return self._cached_states[approp_max], approp_max

@dataclass
class CommandController:
    init_state: T = None
    cache_interval: int = 100
    command_store: CommandStore = field(default_factory=InMemoryCommandStore)
    cursor: int = field(default=0, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self):
        if self.command_store is None:
            self.command_store = InMemoryCommandStore()

        latest_cached, idx = self.command_store.last_cached()
        has_init = latest_cached is not None

        if not has_init and self.init_state is None:
            raise ValueError(f"The init state must be set for command stores that have not been initialized")

        if not has_init and self.init_state is not None:
            self.command_store.add_cached(self.init_state, self.cursor)

        logger.info(f"Init State: {pprint.pformat(latest_cached)}")

        if idx is None:
            self.cursor = 0
        else:
            self.cursor = len(self.command_store.get_commands(start_cursor=idx)) + idx

    def _needsLock(foo):
        def magic(self, *args, **kwargs):
            with self._lock:
                logger.info(f"lock acquired")
                ret = foo(self, *args, **kwargs)
            logger.info(f"Lock released")
            return ret
        return magic

    @_needsLock
    def execute(self, commands: List[CommandProtocol]) -> T:
        # delete any registered commands after the current cursor
        self.command_store.remove_commands(self.cursor + 1)

        # delete any cached states after the current cursor
        for ii, cache in self.command_store.get_cached().items():
            if ii > self.cursor:
                self.command_store.remove_cached_at_cursor(ii)


        # add new commands
        for command in commands:
            self.cursor += 1
            self.command_store.add_command(command, self.cursor)


        logger.info(f"Executing commands {pprint.pformat(commands)} [idx: {self.cursor}]")

        # resolve
        latest_state = self.resolve()

        if self.cursor - max(x for x in self.command_store.get_cached().keys()) >= self.cache_interval:
            self.command_store.add_cached(latest_state, self.cursor)

        return latest_state

    def resolve(self, idx: int = None) -> T:
        command = None

        if idx is None:
            idx = self.cursor

        if idx == 0:
            return self.init_state

        try:
            # Get latest cached
            last_cached_state, last_cached_idx = self.command_store.last_cached(max_idx=idx)

            last_cached_state = copy.deepcopy(last_cached_state)

            for command in self.command_store.get_commands(last_cached_idx, idx):
                last_cached_state = command.execute(last_cached_state)
                if last_cached_state is None:
                    raise Exception("The command.execute() operation returned a None value")


            logger.info(pprint.pformat(last_cached_state))
            return last_cached_state
        except Exception as e:
            # raise the exception on the command that failed
            raise ResolveStateException(command=command, inner=e)

    @_needsLock
    def undo(self) -> T:
        # move cursor back in time
        if self.cursor > 0:
            self.cursor -= 1

        logger.info(f"Undo - [idx: {self.cursor}]")

        state = self.resolve()
        logger.info(pprint.pformat(state))
        return state


    @_needsLock
    def redo(self) -> T:
        # move cursor forward in time
        if self.cursor < len(self.command_store.get_commands()):
            self.cursor += 1

        logger.info(f"Redo - [idx: {self.cursor}]")

        state = self.resolve()
        logger.info(pprint.pformat(state))
        return state


    @property
    def CachedStates(self) -> List[Tuple[T, int]]:
        return [(k, v) for k, v in self.command_store.get_cached().items()]

    @property
    def ActiveCommands(self):
        return self.command_store.get_commands(0, self.cursor)

    @property
    def State(self) -> T:
        return self.resolve()