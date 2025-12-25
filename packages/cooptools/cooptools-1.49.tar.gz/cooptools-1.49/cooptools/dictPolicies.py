from abc import ABC, abstractmethod
from cooptools.toggles import Toggleable
from typing import Type, Dict

class IActOnDictPolicy(ABC):
    def __init__(self, key: str):
        self.key = key

    def act_on_dict(self, dict: Dict, **kwargs):
        if self.key not in dict.keys():
            self.initialize(dict)

        self._act(dict, **kwargs)

    @abstractmethod
    def _act(self, dict: Dict, **kwargs):
        pass

    @abstractmethod
    def initialize(self, dict: Dict):
        pass

    def __eq__(self, other):
        if issubclass(type(other), IActOnDictPolicy) and other.key == self.key:
            return True
        else:
            return False

    def __repr__(self):
        return f"{type(self)} with key [{self.key}]"

    def __hash__(self):
        return hash(self.key)

class DoNothingPolicy(IActOnDictPolicy):
    def __init__(self, key:str):
        IActOnDictPolicy.__init__(self, key)

    def _act(self, dict: Dict, **kwargs):
        pass

    def initialize(self, dict: Dict):
        pass

class TogglePolicy(IActOnDictPolicy):
    def __init__(self, key: str, toggle_type: Type[Toggleable], **toggle_kwargs):
        IActOnDictPolicy.__init__(self, key)
        self.toggle_type = toggle_type
        self.toggle_kwargs = toggle_kwargs

    def _act(self, dict: Dict, **kwargs):
        dict[self.key].toggle()

    def initialize(self, dict: Dict):
        dict[self.key] = dict.setdefault(self.key, self.toggle_type(**self.toggle_kwargs))

class IncrementPolicy(IActOnDictPolicy):
    def __init__(self, key: str, starting_index: int = 0, step_size: int = 1):
        IActOnDictPolicy.__init__(self, key)
        self.starting_index = starting_index
        self.step_size = step_size

    def _act(self, dict: Dict, **kwargs):
        dict[self.key] = dict[self.key] + self.step_size

    def initialize(self, dict: Dict):
        dict[self.key] = self.starting_index

class SetValuePolicy(IActOnDictPolicy):
    def __init__(self, key: str, starting_index: int = 0, step_size: int = 1):
        IActOnDictPolicy.__init__(self, key)
        self.starting_index = starting_index
        self.step_size = step_size

    def _act(self, dict: Dict, **kwargs):
        if 'value' not in kwargs.keys():
            raise Exception(f"Value must be provided for act_on_gridstate on {type(self)}")
        dict[self.key] = kwargs['value']

    def initialize(self, dict: Dict):
        dict[self.key] = None