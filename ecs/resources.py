from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from camera.camera import Camera
    from map.map import GameMap
    from terminal.terminal import GlaiveTerminal
    from ui.state import UIState

T = TypeVar("T")


@dataclass
class Resource(Generic[T]):
    instance: T


@dataclass
class TerminalResource(Resource["GlaiveTerminal"]):
    pass


@dataclass
class MapResource(Resource["GameMap"]):
    pass


@dataclass
class CameraResource(Resource["Camera"]):
    pass


@dataclass
class UIResource(Resource["UIState"]):
    pass


@dataclass
class LookModeResource:
    """Tracks look mode state for cursor-based map exploration"""

    active: bool = False
    cursor_x: int = 0
    cursor_y: int = 0
