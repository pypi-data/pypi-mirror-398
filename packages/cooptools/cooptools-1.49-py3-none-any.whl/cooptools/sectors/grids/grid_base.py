from typing import Dict, List, Tuple, Any, Set, Callable
import numpy as np
from cooptools.dictPolicies import IActOnDictPolicy, DoNothingPolicy
from cooptools.sectors.grids.gridState import GridState
from pprint import pformat
from cooptools.common import flattened_list_of_lists
from cooptools.coopEnum import CardinalPosition

dict_evaluator = Callable[[Dict], str]

class Grid:
    def __init__(self,
                 nRows: int,
                 nColumns: int,
                 values: np.array = None,
                 default_state: Dict=None
                 ):
        self.nRows = nRows
        self.nColumns = nColumns
        self.grid = np.array([[GridState(self, row, column, values[row][column]) if values is not None else GridState(self, row, column, state=default_state)
                               for column in range(self.nColumns)] for row in range(self.nRows)])

    def __str__(self):
        ret = f"<{self.nRows} x {self.nColumns}> of type {type(self.grid[0][0])}"
        ret += f"\n{pformat(self.grid)}"

        return ret

    def __getitem__(self, item):
        return self.grid[item]

    def __iter__(self):
        return self.grid_enumerator

    @property
    def GridKeys(self) -> List:
        return flattened_list_of_lists([gs.state.keys() for _, gs in self.grid_enumerator],
                                       unique=True)

    @property
    def grid_enumerator(self) -> (Tuple[int, int], GridState):
        for row in range(0, self.nRows):
            for col in range(0, self.nColumns):
                yield ((row, col), self.grid[row][col])

    @property
    def Shape(self):
        return self.grid.shape

    def at(self, row, column):
        return self.grid[row][column]

    def _init_a_new_policy(self, policy: IActOnDictPolicy):
        for pos, state in self.grid_enumerator:
            policy.initialize(state.state)

    def act_at_loc(self, row: int, column: int, policies:List[IActOnDictPolicy]):
        for policy in policies:
            if policy.key not in self.grid[row][column].state.keys():
                self._init_a_new_policy(policy)
            policy.act_on_dict(self.grid[row][column].state)

        return self.grid[row][column]

    def filtered_array_by_keys(self, keys: List[str]):
        return np.array([[
            {key: self.grid[row][column].state[key] for key in keys}
                            for column in range(self.nColumns)]
                            for row in range(self.nRows)])

    def state_value_as_array(self, key: str):
        return np.array([[self.grid[row][column].state[key]
                            for column in range(self.nColumns)]
                            for row in range(self.nRows)])

    def _eqls_or_in(self, val, collection):
        if type(collection) in [Set, List]:
            return val in collection
        else:
            return val == collection

    def coords_with_condition(self, rules: List[dict_evaluator]):
        passes = []
        for ii in self:
            for rule in rules:
                if rule(ii[1].state):
                    passes.append(ii[0])
        return passes

    def coord_from_grid_pos(self,
                            grid_pos: Tuple[int, int],
                            area_wh:Tuple[float, float],
                            cardinal_pos: CardinalPosition= CardinalPosition.TOP_LEFT) -> Tuple[float, float]:
        pass

if __name__ == "__main__":
    import coopstructs.grids.gridSelectPolicies as policies
    from cooptools.toggles import BooleanToggleable, IntegerRangeToggleable
    grid = Grid(10, 10, default_state={"a": 1, "b": 2, "c": "Hello"})
    actions = [
        policies.IncrementPolicy(key='a'),
        policies.TogglePolicy(key='toggled', toggle_type=IntegerRangeToggleable, starting_value=3, min=2, max=5)
    ]
    grid.act_at_loc(5, 5, actions)
    grid.act_at_loc(7, 7, actions)

    res = grid.coords_with_condition(rules=[lambda d: d['a'] == 2])
    print(res)

    print(grid)