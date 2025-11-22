from dataclasses import dataclass

from terminal.glyph import Glyph


class Component:
    pass


@dataclass
class IsPlayer(Component):
    pass


@dataclass
class TurnConsumed(Component):
    pass


@dataclass
class Position(Component):
    x: int
    y: int


@dataclass
class Drawable(Component):
    glyph: Glyph
    name: str


@dataclass
class MoveIntent(Component):
    dx: int
    dy: int
    consumes_turn: bool
