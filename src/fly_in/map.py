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
class Metadata:
    zone: Zone
    color: Color
    max_link_capacity: int
    max_drones: int


@dataclass
class Node:
    name: str
    x: int
    y: int
    metadata: Metadata


@dataclass
class Connection:
    name1: Node
    name2: Node
    metadata: Metadata


class Map():
    def __init__(self,
                 start_hub: Node,
                 end_hud: Node,
                 hubs: tuple[Node]):
        self.start_hub: Node = start_hub
        self.end_hud: Node = end_hud
        self.hubs: tuple[Node] = hubs
