"""Module for all types of Fly-in."""
from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum, auto


class Zone(Enum):
    """Enum for all possible Zone types."""

    NORMAL = auto()
    RESTRICTED = auto()
    PRIORITY = auto()
    BLOCKED = auto()

    @staticmethod
    def get_zone(zone_str: str) -> Optional['Zone']:
        """Check if zone_str exists in enum.

        Returns:
            Zone | None: Zone enum value or None if not found
        """
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


@dataclass(frozen=True)
class Metadata:
    """A dataclass representing Metadata."""

    zone: Optional[Zone]
    color: Optional[str]
    max_link_capacity: Optional[int]
    max_drones: Optional[int]


@dataclass(frozen=True)
class Node:
    """A dataclass representing a Node."""

    name: str
    x: int
    y: int
    metadata: Metadata


@dataclass(frozen=True)
class Connection:
    """A dataclass representing a Connection."""

    node1: Node
    node2: Node
    metadata: Metadata

    def __eq__(self, other: Any) -> bool:
        """Compare Connections the correct way using associated nodes.

        Args:
            other (Any): The object to compare with

        Returns:
            bool: True if Connections are equals, False if not
        """
        if not isinstance(other, Connection):
            return NotImplemented
        return frozenset([self.node1,
                          self.node2]) == frozenset([other.node1, other.node2])

    def __hash__(self) -> int:
        """Hash dataclass the correct way by using associated nodes.

        Returns:
            int: hash
        """
        return hash(frozenset([self.node1, self.node2]))


@dataclass
class Map:
    """A dataclass representing a Map."""

    nb_drones: int
    start_hub: Node
    end_hub: Node
    hubs: list[Node]
    connections: set[Connection]
