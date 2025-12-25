from typing import List, Callable, Any, Type
from enum import Enum

class Toggleable:
    def __init__(self,
                 values: List,
                 starting_index: int = 0,
                 starting_value: Any = None,
                 on_toggle_callbacks: List[Callable[[], Any]] = None):
        # TODO: Values is better as a generator. This allows for user to provide an "infinite" list and not provide all values to memory
        self.values = values
        self.index = 0
        self.on_toggle_callbacks = on_toggle_callbacks

        if starting_value and starting_value in values: self.index = self.values.index(starting_value)
        if starting_index and starting_index < len(values): self.index = starting_index

    def toggle(self,
               on_toggle_callbacks: List[Callable[[Any], Any]] = None,
               reverse: bool = False,
               loop: bool = True):
        if reverse:
            self.index -= 1
        else:
            self.index += 1

        if self.index >= len(self.values) and loop:
            self.index = 0
        elif self.index >= len(self.values):
            self.index = len(self.values) - 1

        if self.index < 0 and loop:
            self.index = len(self.values) - 1
        elif self.index < 0:
            self.index = 0

        if self.on_toggle_callbacks is not None:
            [x(self.value) for x in self.on_toggle_callbacks]

        if on_toggle_callbacks is not None:
            [x(self.value) for x in on_toggle_callbacks]

        return self.value

    @property
    def value(self):
        return self.values[self.index]

    def __repr__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def copy(self):
        return type(self)(values=self.value, starting_index=self.index)

    def set_value(self, value, on_toggle_callbacks: List[Callable[[Any], Any]] = None):
        self.index = self.values.index(value)

        if self.on_toggle_callbacks is not None:
            [x(self.value) for x in self.on_toggle_callbacks]

        if on_toggle_callbacks is not None:
            [x(self.value) for x in on_toggle_callbacks]



class BooleanToggleable(Toggleable):
    def __init__(self, default: bool = True,
                 on_toggle_callbacks: List[Callable[[Any], Any]] = None):
        if default:
            index = 1
        else:
            index = 0

        Toggleable.__init__(self, [False, True], index, on_toggle_callbacks)

    @property
    def is_on(self):
        return self.value

    def copy(self):
        default = True if self.index == 1 else False
        return type(self)(default=default)

    def __add__(self, other):
        return any([self.value, other.value])

    def __gt__(self, other):
        if self.value and not other.value:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.value or self.value == other.value == False:
            return True
        else:
            return False

    def __le__(self, other):
        if other.value or self.value == other.value == False:
            return True
        else:
            return False

    def __lt__(self, other):
        if not self.value and other.value:
            return True
        else:
            return False

    def __eq__(self, other):
        if type(other) == type(BooleanToggleable):
            return other.value == self.value
        elif type(other) == bool:
            return other == self.value


class IntegerRangeToggleable(Toggleable):
    def __init__(self,
                 min: int,
                 max: int,
                 step_size: int = 1,
                 on_toggle_callbacks: List[Callable[[Any], Any]] = None,
                 starting_value: int = None):
        if starting_value is not None and \
                ((not (min <= starting_value <= max)) or
                 ((starting_value - min) % step_size != 0)):
            raise ValueError(
                f"The starting value provided {starting_value} was not between {min} and {max} and on the step of size {step_size}")

        starting_index = 0 if not starting_value else starting_value - min

        Toggleable.__init__(self,
                            values=[ii for ii in range(min, max + 1, step_size)],
                            on_toggle_callbacks=on_toggle_callbacks,
                            starting_index=starting_index)

        self.min = min
        self.max = max
        self.step = step_size

    def copy(self):
        return type(self)(min=self.min, max=self.max, step_size=self.step)


class EnumToggleable(Toggleable):
    def __init__(self,
                 enum_type: Type[Enum],
                 default=None,
                 on_toggle_callbacks: List[Callable[[Any], Any]] = None):
        self.enum = enum_type
        Toggleable.__init__(self, [val for val in enum_type.__members__.values()], 0, on_toggle_callbacks)
        if default is not None:
            self.set_value(default)


