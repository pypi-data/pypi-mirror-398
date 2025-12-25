from dataclasses import dataclass
from typing import Tuple
from cooptools.coopEnum import CardinalPosition

@dataclass(frozen=True)
class Anchor2D:
    pt: Tuple[float, float]
    dims: Tuple[float, float]
    cardinality: CardinalPosition = CardinalPosition.BOTTOM_LEFT
    inverted_y: bool = False

    def __post_init__(self):
        if self.cardinality is None:
            object.__setattr__(self, 'cardinality', CardinalPosition.BOTTOM_LEFT)

    @classmethod
    def from_anchor(cls,
                    anchor,
                    pt: Tuple[float, ...] = None,
                    cardinality: CardinalPosition = None,
                    dims: Tuple[float, float] = None,
                    inverted_y: bool = None):
        return Anchor2D(
            pt=pt if pt is not None else anchor.pt,
            cardinality=cardinality if cardinality is not None else anchor.cardinality,
            dims=dims if dims is not None else anchor.dims,
            inverted_y=inverted_y if inverted_y is not None else anchor.inverted_y
        )

    def pos(self, cardinality: CardinalPosition = None):
        if cardinality is None:
            cardinality = self.cardinality

        return CardinalPosition.alignment_conversion(dims=self.dims,
                                                     anchor=self.pt,
                                                     from_cardinality=self.cardinality,
                                                     to_cardinality=cardinality,
                                                     inverted_y=self.inverted_y)

    def corner_generator(self):
        yield self.pos(CardinalPosition.BOTTOM_LEFT)
        yield self.pos(CardinalPosition.TOP_LEFT)
        yield self.pos(CardinalPosition.TOP_RIGHT)
        yield self.pos(CardinalPosition.BOTTOM_RIGHT)

    @property
    def Corners(self):
        return {
            CardinalPosition.TOP_LEFT: self.pos(cardinality=CardinalPosition.TOP_LEFT),
            CardinalPosition.TOP_RIGHT: self.pos(cardinality=CardinalPosition.TOP_RIGHT),
            CardinalPosition.BOTTOM_RIGHT: self.pos(cardinality=CardinalPosition.BOTTOM_RIGHT),
            CardinalPosition.BOTTOM_LEFT: self.pos(cardinality=CardinalPosition.BOTTOM_LEFT),
        }

    @property
    def CardinalPositions(self):
        return {
            x: self.pos(cardinality=x) for x in list(CardinalPosition)
        }
