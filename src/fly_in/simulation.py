from collections import defaultdict
import heapq
import itertools
from fly_in.map_types import Node, Connection, Zone, Map
from typing import TypeAlias


Path: TypeAlias = list[tuple[Node | Connection, int]]


class SimulationState:
    def __init__(self, start_hub: Node, end_hub: Node, nb_drones: int) -> None:
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
        if node == self.end_hub or node == self.start_hub:
            return True
        capacity: int = node.metadata.max_drones \
            if node.metadata.max_drones else 1

        nb_drones_in: int = len(self.node_reservations
                                .get(time, {}).get(node, []))
        return nb_drones_in < capacity

    def can_use_connection(self, connection: Connection, time: int) -> bool:
        capacity: int = connection.metadata.max_link_capacity \
            if connection.metadata.max_link_capacity else 1
        nb_drones_on: int = len(self.conn_reservations
                                .get(time, {}).get(connection, []))
        return nb_drones_on < capacity

    def reserve_node(self, node: Node, time: int, drone_id: int) -> None:
        self.node_reservations[time][node].append(drone_id)

    def reserve_connection(self, connection: Connection,
                           time: int, drone_id: int) -> None:
        self.conn_reservations[time][connection].append(drone_id)


class PathFinder:
    def __init__(self, map_data: Map) -> None:
        self.map = map_data
        self.state = SimulationState(map_data.start_hub, map_data.end_hub,
                                     map_data.nb_drones)
        self.drones_paths: dict[int, Path] = {}

    def route_all_drones(self) -> None:
        for drone_id in range(1, self.map.nb_drones + 1):
            path = self.find_path(drone_id)
            if path:
                self._reserve_path(drone_id, path)
                self.drones_paths.update({
                    drone_id: path
                })
            else:
                print("no path for ", drone_id)
        pass

    def _reserve_path(self, drone_id: int,
                      path: Path) -> None:
        for location, time in path:
            if isinstance(location, Node):
                self.state.reserve_node(location, time, drone_id)
            elif isinstance(location, Connection):
                self.state.reserve_connection(location, time, drone_id)

    def _heuristic(self, node: Node) -> int:
        return (abs(node.x - self.map.end_hub.x)
                + abs(node.y - self.map.end_hub.y))

    def find_path(self, drone_id: int) -> Path:
        counter: itertools.count[int] = itertools.count()

        start_g = 0.0
        start_h = self._heuristic(self.map.start_hub)
        open_set: list[tuple[float, int, float, int, Node, Path]] = [
            (start_g + start_h, next(counter), start_g,
             0, self.map.start_hub, [(self.map.start_hub, 0)])
        ]
        visited = set()

        while open_set:
            f_score, _, g_score, current_time, current_node, path = \
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
                if dest_node.metadata.zone:
                    if dest_node.metadata.zone == Zone.RESTRICTED:
                        cost = 2.0
                        restricted = 1
                    elif dest_node.metadata.zone == Zone.PRIORITY:
                        cost = 0.1

                if self.state.can_use_connection(conn, next_time) \
                    and self.state.can_enter_node(dest_node,
                                                  next_time + restricted):
                    new_path = path + [(conn, next_time)] \
                        + [(dest_node, next_time + restricted)]
                    new_g = g_score + cost
                    new_f = new_g + self._heuristic(dest_node)
                    heapq.heappush(open_set,
                                   (new_f,
                                    next(counter),
                                    new_g,
                                    next_time + restricted,
                                    dest_node, new_path))

        return []
