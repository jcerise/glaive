from dataclasses import dataclass
from typing import Any


@dataclass
class Resource:
    instance: Any


@dataclass
class TerminalResource(Resource):
    pass


@dataclass
class MapResource(Resource):
    pass
