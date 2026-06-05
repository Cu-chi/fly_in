"""Module for output of Fly-in."""
from fly_in.simulation import Path
from fly_in.map_types import Connection, Node


class Output:
    """A class representing an Output object."""

    def __init__(self, drones_paths: dict[int, Path]) -> None:
        """Initialize an Output object.

        Args:
            drones_paths (dict[int, Path]): the drones paths
        """
        self.set_drones_paths(drones_paths)

    def set_drones_paths(self, drones_paths: dict[int, Path]) -> None:
        """Set the drones paths.

        Args:
            drones_paths (dict[int, Path]): the drones paths
        """
        self.__drones_paths = drones_paths

    def from_positions_print_turns(self,
                                   positions: list[
                                       dict[int, Node | Connection]]) -> None:
        """Use list of positions to print turns.

        Args:
            positions (list[ dict[int, Node  |  Connection]]): the list of
            positions
        """
        for step_data in positions:
            turn: str = ""
            for drone_id, last_pos in step_data.items():
                turn += f" D{drone_id}-"
                if isinstance(last_pos, Node):
                    turn += last_pos.name
                elif isinstance(last_pos, Connection):
                    turn += f"{last_pos.node1.name}-{last_pos.node2.name}"
            print(turn.strip())

    def generate_list_of_positions(self) -> list[dict[int, Node | Connection]]:
        """Generate a list of positions for each turn and for each drones.

        Returns:
            list[dict[int, Node | Connection]]: the list of positions
        """
        path_found = True
        step = 0
        positions: list[dict[int, Node | Connection]] = []
        start: Node | Connection = self.__drones_paths[1][0][0]
        while path_found:
            path_found = False
            for drone_id in self.__drones_paths:
                path: Path = list(filter(lambda p: p[1] == step + 1,
                                         self.__drones_paths[drone_id]))
                if not path:
                    continue
                last_pos: Node | Connection = path[-1][0]
                if last_pos is start:
                    continue
                if len(positions) - 1 < step:
                    positions.append({})
                path_found = True
                positions[step][drone_id] = last_pos
            step += 1
        return positions
