"""Module for simulation, path-finding of Fly-in."""
from collections import defaultdict
import heapq
import itertools
from fly_in.map_types import Node, Connection, Zone, Map
from typing import TypeAlias, Any
import sys


PathStep: TypeAlias = tuple[Node | Connection, int]
Path: TypeAlias = list[PathStep]


class PathError(Exception):
    """Class for PathError."""

    def __init__(self, *args: Any) -> None:
        """Initialize a PathError exception."""
        super().__init__(*args)


class SimulationState:
    """A class representing a SimulationState."""

    def __init__(self, start_hub: Node, end_hub: Node, nb_drones: int) -> None:
        """Initialize a SimulationState object.

        Args:
            start_hub (Node): start hub
            end_hub (Node): end hub
            nb_drones (int): number of drones
        """
        self.start_hub = start_hub
        self.end_hub = end_hub
        self.nb_drones = nb_drones

        self.node_reservations: dict[int, dict[Node, list[int]]] = \
            defaultdict(lambda: defaultdict(list))
        self.conn_reservations: dict[int, dict[Connection, list[int]]] = \
            defaultdict(lambda: defaultdict(list))

        self.node_reservations[0][self.start_hub] = list(
            range(1, nb_drones + 1))

    def can_enter_node(self, node: Node, time: int) -> bool:
        """Check if the node can be used at a given turn.

        Args:
            node (Node): node to check
            time (int): time (turn)

        Returns:
            bool: True if usable, False is not
        """
        if node == self.end_hub or node == self.start_hub:
            return True
        capacity: int = node.metadata.max_drones \
            if node.metadata.max_drones else 1

        nb_drones_in: int = len(self.node_reservations
                                .get(time, {}).get(node, []))
        return nb_drones_in < capacity

    def can_use_connection(self, connection: Connection, time: int) -> bool:
        """Check if the connection can be used at a given turn.

        Args:
            connection (Connection): connection to check
            time (int): time (turn)

        Returns:
            bool: True if usable, False is not
        """
        capacity: int = connection.metadata.max_link_capacity \
            if connection.metadata.max_link_capacity else 1
        nb_drones_on: int = len(self.conn_reservations
                                .get(time, {}).get(connection, []))
        return nb_drones_on < capacity

    def reserve_node(self, node: Node, time: int, drone_id: int) -> None:
        """Reserve a node at a given turn for a given drone id.

        Args:
            node (Node): node to reserve
            time (int): time (turn)
            drone_id (int): drone id
        """
        self.node_reservations[time][node].append(drone_id)

    def reserve_connection(self, connection: Connection,
                           time: int, drone_id: int) -> None:
        """Reserve a connection at a given turn for a given drone id.

        Args:
            connection (Connection): connection to reserve
            time (int): time (turn)
            drone_id (int): drone id
        """
        self.conn_reservations[time][connection].append(drone_id)


class PathFinder:
    """A class representing a PathFinder."""

    def __init__(self, map_data: Map) -> None:
        """Initialize a PathFinder object.

        Args:
            map_data (Map): Map object

        Raises:
            PathError: In case of not solvable map
        """
        self.map = map_data
        self.state = SimulationState(map_data.start_hub, map_data.end_hub,
                                     map_data.nb_drones)
        self.drones_paths: dict[int, Path] = {}
        self.true_dist = self._compute_true_distances()
        if self.true_dist[self.map.start_hub] == -1:
            raise PathError("map is not solvable")

    def route_all_drones(self) -> None:
        """Find a path for all drones using the find_path method."""
        for drone_id in range(1, self.map.nb_drones + 1):
            path = self.find_path()
            if path:
                self._reserve_path(drone_id, path)
                self.drones_paths.update({
                    drone_id: path
                })
            else:
                print("no path for ", drone_id, file=sys.stderr)

    def _compute_true_distances(self) -> dict[Node, int]:
        distances: dict[Node, int] = {node: -1
                                      for node in self.map.hubs}
        distances[self.map.end_hub] = 0

        counter = itertools.count()
        queue = [(0, next(counter), self.map.end_hub)]

        while queue:
            dist, _, current = heapq.heappop(queue)

            if dist > distances[current] or distances[current] == -1:
                continue

            for conn in self.map.connections:
                neighbor = None
                if conn.node1 == current:
                    neighbor = conn.node2
                elif conn.node2 == current:
                    neighbor = conn.node1

                if neighbor:
                    if neighbor.metadata.zone == Zone.BLOCKED:
                        continue

                    new_dist = dist + 1
                    if distances[neighbor] == -1 or \
                       new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        heapq.heappush(queue,
                                       (new_dist, next(counter), neighbor))
        return distances

    def _reserve_path(self, drone_id: int,
                      path: Path) -> None:
        for location, time in path:
            if isinstance(location, Node):
                self.state.reserve_node(location, time, drone_id)
            elif isinstance(location, Connection):
                self.state.reserve_connection(location, time, drone_id)

    def _heuristic(self, node: Node) -> int:
        return self.true_dist[node]

    def find_path(self) -> Path:
        """Find a path based on current reservations from SimulationState.

        Returns:
            Path: path from start to end
        """
        counter: itertools.count[int] = itertools.count()

        start_g = 0.0
        start_h = self._heuristic(self.map.start_hub)
        open_set: list[tuple[float, int, float, int, Node, Path]] = [
            (start_g + start_h, next(counter), start_g,
             0, self.map.start_hub, [(self.map.start_hub, 0)])
        ]
        visited = set()

        while open_set:
            _, _, g_score, current_time, current_node, path = \
                heapq.heappop(open_set)

            if current_node == self.map.end_hub:
                return path

            state_key = (current_node, current_time)
            if state_key in visited:
                continue
            visited.add(state_key)

            next_time = current_time + 1
            if self.state.can_enter_node(current_node, next_time):
                new_path = path + [(current_node, next_time)]
                new_g = g_score + 1.0
                new_f = new_g + self._heuristic(current_node)
                heapq.heappush(open_set,
                               (new_f, next(counter), new_g, next_time,
                                current_node, new_path))

            for conn in self.map.connections:
                dest_node = None
                if conn.node1 == current_node:
                    dest_node = conn.node2
                elif conn.node2 == current_node:
                    dest_node = conn.node1

                if dest_node is None:
                    continue
                if dest_node.metadata.zone:
                    if dest_node.metadata.zone == Zone.BLOCKED:
                        continue

                cost: float = 1.0
                restricted: int = 0
                priority_bonus: float = 0.0
                if dest_node.metadata.zone:
                    if dest_node.metadata.zone == Zone.RESTRICTED:
                        cost = 2.0
                        restricted = 1
                    elif dest_node.metadata.zone == Zone.PRIORITY:
                        priority_bonus = 0.5

                if self.state.can_use_connection(conn, next_time) \
                    and self.state.can_enter_node(dest_node,
                                                  next_time + restricted):
                    new_path = path + [(conn, next_time)] \
                        + [(dest_node, next_time + restricted)]
                    new_g = g_score + cost
                    new_f = new_g + self._heuristic(dest_node) - priority_bonus
                    heapq.heappush(open_set,
                                   (new_f,
                                    next(counter),
                                    new_g,
                                    next_time + restricted,
                                    dest_node, new_path))

        return []
