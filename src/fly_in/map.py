from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto


class Zone(Enum):
    NORMAL = auto()
    RESTRICTED = auto()
    PRIORITY = auto()
    BLOCKED = auto()

    @staticmethod
    def get_zone(zone_str: str) -> Optional['Zone']:
        match zone_str:
            case "normal":
                return Zone.NORMAL
            case "restricted":
                return Zone.RESTRICTED
            case "priority":
                return Zone.PRIORITY
            case "blocked":
                return Zone.BLOCKED
            case _:
                return None


class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    YELLOW = auto()
    PINK = auto()

    @staticmethod
    def get_color(color_str: str) -> Optional['Color']:
        match color_str:
            case "red":
                return Color.RED
            case "green":
                return Color.GREEN
            case "blue":
                return Color.BLUE
            case "yellow":
                return Color.YELLOW
            case "pink":
                return Color.PINK
            case _:
                return None


@dataclass
class Metadata:
    zone: Optional[Zone]
    color: Optional[Color]
    max_link_capacity: Optional[int]
    max_drones: Optional[int]


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
