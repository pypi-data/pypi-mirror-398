""" A Python Class
A simple Python graph class, demonstrating the essential
facts and functionalities of graphs.
"""
from typing import List, Dict, Callable, Tuple, Iterable, Self
import uuid
import logging
import copy
import cooptools.geometry_utils.vector_utils as vec
from dataclasses import dataclass
import json
from cooptools.protocols import UniqueIdentifier

logger = logging.getLogger(__name__)

class Node(object):
    def __init__(self, name:str, pos: Tuple[float, ...]):
        if not isinstance(pos, Tuple) :
            raise TypeError(f"position must be of type {type(Tuple[float, ...])}, but {type(pos)} was provided")

        self.name = name
        self.pos = pos

    def __str__(self):
        return f"{str(self.name)} at {self.pos}"

    def __eq__(self, other):
        if isinstance(other, Node) and other.name == self.name:
            return True
        else:
            return False

    def __hash__(self):
        return hash(str(self.name))

    def __repr__(self):
        return self.__str__()

    def as_jsonable_dict(self):
        return {
            f'{self.name=}'.split('=')[0].replace('self.', ''): self.name,
            f'{self.pos=}'.split('=')[0].replace('self.', ''): self.pos,
        }

    @staticmethod
    def from_json(data):
        return Node(data["name"], tuple(data["pos"]))

class Edge(object):
    def __init__(self,
                 nodeA: Node,
                 nodeB: Node,
                 edge_cost: float = None,
                 naming_provider: Callable[[], str] = None,
                 disablers: Iterable = None,
                 length: float = None):
        self.start = nodeA
        self.end = nodeB
        self._disablers = set()
        self.length = length if length is not None else vec.distance_between(nodeA.pos, nodeB.pos)
        self.id = naming_provider() if naming_provider else str(uuid.uuid4())
        self.cost = edge_cost if edge_cost is not None else self.length

        if self.cost < 0:
            raise ValueError(f"An Edge Cost cannot be negative")

        if disablers is not None:
            [self.add_disabler(x) for x in disablers]

    def __str__(self):
        return f"{self.id}: {self.start.name}-->{self.end.name}"

    def __hash__(self):
        return hash(str(self.id))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Edge) and other.id == self.id:
            return True
        else:
            return False

    def matches_profile_of(self, other):
        if isinstance(other, Edge) and other.start == self.start and self.end == other.end:
            return True
        else:
            return False

    def eucledian_distance(self):
        return self.length

    def enabled(self, ignored_disablers: set = None):
        if ignored_disablers is None:
            ignored_disablers = set()
        return self._disablers.issubset(ignored_disablers)


    def remove_disabler(self, disabler):
        self._disablers.discard(disabler)

    def add_disabler(self, disabler):
        self._disablers.add(disabler)

    def config_match(self, other):
        if isinstance(other, Edge) and other.start == self.start and other.end == self.end and other._disablers == self._disablers:
            return True
        else:
            return False

    def disablers(self):
        return copy.deepcopy(self._disablers)

    def as_jsonable_dict(self):
        return {
            f'{self.id=}'.split('=')[0].replace('self.', ''): self.id,
            f'{self.start=}'.split('=')[0].replace('self.', ''): self.start.name,
            f'{self.end=}'.split('=')[0].replace('self.', ''): self.end.name,
            f'{self._disablers=}'.split('=')[0].replace('self.', '').replace("_", ""): list(self._disablers),
            f'{self.length=}'.split('=')[0].replace('self.', ''): self.length,
            f'{self.cost=}'.split('=')[0].replace('self.', ''): self.cost,
        }

    @property
    def Length(self) -> float:
        return self.length

    @property
    def Cost(self) -> float:
        return self.cost

    def reversed(self):
        return Edge(
                nodeA=self.end,
                nodeB=self.start,
                edge_cost=self.cost,
                naming_provider=lambda: self.id
            )

class EdgeAlreadyExistsException(Exception):
    def __init__(self,
                 edge: Edge):
        self.edge = edge
        err = f"Edge with id: {self.edge.id} already exists"
        logger.error(err)
        super().__init__(err)

class AStarMetrics():
    def __init__(self, parent, graph_node: Node, edge: Edge):
        if not (isinstance(parent, AStarMetrics) or parent is None):
            raise TypeError(f"Astar parent must be AStarNode or None, {type(parent)} was given")

        # if not (isinstance(graph_node, Node)):
        #     raise TypeError(f"Astar graph_node must be Node, {type(graph_node)} was given")

        self.parent = parent
        self.graph_node = graph_node
        self.edge = edge
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        if isinstance(other, AStarMetrics) and other.graph_node == self.graph_node:
            return True
        else:
            return False

    def __hash__(self):
        return self.graph_node.__hash__()

    def __repr__(self):
        return f"{self.graph_node} g: {self.g} h: {self.h} f: {self.f}"

    def to_json(self):
        return {
            "node_id": self.graph_node.name,
            "parent_id": self.parent.graph_node.name if self.parent else None,
            "g": self.g,
            "h": self.h,
            "f": self.f,
        }

    @staticmethod
    def from_json(data, node_lookup, metrics_lookup):
        node = node_lookup[data["node_id"]]
        parent = metrics_lookup.get(data["parent_id"])
        m = AStarMetrics(parent, node, edge=None)
        m.g = data["g"]
        m.h = data["h"]
        m.f = data["f"]
        return m


@dataclass(frozen=True, slots=True)
class AStarResults:
    nodes: Iterable[Node]
    edges: Iterable[Edge]
    steps: Dict[int, Dict]
    source: Node
    dest: Node
    disabled_node_ids: List[str] = None

    def __post_init__(self):
        if self.edges is not None and None in self.edges:
            raise Exception(f"edges cannot contain a None value")

    @property
    def Length(self):
        return sum(x.Length for x in self.edges if x is not None)

    @property
    def Cost(self):
        return sum(x.Cost for x in self.edges if x is not None)


    def to_json(self) -> str:
        # collect all nodes
        nodes = {n.name: n for n in self.path} if self.path is not None else {}
        for step in self.steps.values():
            for s in ("open_set", "closed_set"):
                for m in step[s]:
                    nodes[m.graph_node.name] = m.graph_node

        data = {
            "nodes": {k: v.as_jsonable_dict() for k, v in nodes.items()},
            "path": [n.name for n in self.path] if self.path is not None else None,
            "steps": {},
            "source": self.source.name,
            "dest": self.dest.name,
            "disabled_node_ids": list(self.disabled_node_ids),
        }

        for k, step in self.steps.items():
            data["steps"][k] = {
                "open_set": [m.to_json() for m in step["open_set"]],
                "closed_set": [m.to_json() for m in step["closed_set"]],
                "current_item": step["current_item"].to_json()
                if step["current_item"]
                else None,
            }

        return data

    @staticmethod
    def from_json(s: str):
        raw = json.loads(s)

        node_lookup = {
            nid: Node.from_json(n)
            for nid, n in raw["nodes"].items()
        }

        steps = {}
        for k, step in raw["steps"].items():
            metrics_lookup = {}

            def build(m):
                if m["node_id"] not in metrics_lookup:
                    metrics_lookup[m["node_id"]] = AStarMetrics.from_json(
                        m, node_lookup, metrics_lookup
                    )
                return metrics_lookup[m["node_id"]]

            steps[int(k)] = {
                "open_set": {build(m) for m in step["open_set"]},
                "closed_set": {build(m) for m in step["closed_set"]},
                "current_item": build(step["current_item"])
                if step["current_item"]
                else None,
            }

        return AStarResults(
            path=[node_lookup[n] for n in raw["path"]],
            edges=[],
            steps=steps,
            source=node_lookup[raw["source"]],
            dest=node_lookup[raw["dest"]],
            disabled_node_ids=raw["disabled_node_ids"],
        )

