from dataclasses import dataclass


class Component:
    pass


@dataclass
class Position(Component):
    x: int
    y: int


@dataclass
class Drawable(Component):
    char: str
    color: str
    name: str
