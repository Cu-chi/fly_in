from dataclasses import dataclass
from typing import Any
from enum import Enum, auto


class Zone(Enum):
    NORMAL = auto()
    RESTRICTED = auto()
    PRIORITY = auto()
    BLOCKED = auto()


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    YELLOW = auto()
    PINK = auto()


@dataclass
class Node:
    name: str
    x: int
    y: int
    zone: Zone


class Map():
    def __init__(self,
                 start_hub: Node,
                 end_hud: Node,
                 hubs: tuple[Node]):
        self.start_hub: Node = start_hub
        self.end_hud: Node = end_hud
        self.hubs: tuple[Node] = hubs
