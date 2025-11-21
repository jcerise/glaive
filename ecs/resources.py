from dataclasses import dataclass
from typing import Any


@dataclass
class Resource:
    instance: Any


@dataclass
class TerminalResource(Resource)
