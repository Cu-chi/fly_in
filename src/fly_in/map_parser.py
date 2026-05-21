from fly_in.map_types import Node, Metadata, Color, Zone, Connection
from typing import Any
from types import TracebackType


class MapParsingError(Exception):
    def __init__(self, line: int, error: str, *args: Any):
        self.line = line
        self.error = error
        super().__init__(*args)


class MapParser():
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.nb_drones: int | None = None
        self.start_hub: Node | None = None
        self.end_hub: Node | None = None
        self.hubs: list[Node] = []
        self.connections: set[Connection] = set()

    def __enter__(self) -> 'MapParser':
        self.file = open(self.filename, "r")
        self._parser()
        return self

    @staticmethod
    def _extract_metadata_str(id: int, line: str) -> tuple[str, str]:
        """Extract metadata from the line and return
        line without metadata and metadata without brackets

        Args:
            line (str): the line

        Returns:
            tuple[str, str]: first is the line without metadata,
            second is only the metadata without brackets
        """
        opening = line.find("[")
        if opening == -1:
            return line, ""
        metadata_str: str = line[opening:].strip()

        if metadata_str[-1] != "]":
            raise MapParsingError(id, "metadata must be the last argument")
        return line[:opening], metadata_str[1:-1]

    def _get_node_from_name(self, name: str) -> Node | None:
        for hub in self.hubs:
            if hub.name == name:
                return hub
        return None

    def _are_coords_taken(self, x: int, y: int) -> bool:
        if self.start_hub and self.start_hub.x == x and self.start_hub.y == y:
            return True
        if self.end_hub and self.end_hub.x == x and self.end_hub.y == y:
            return True
        for hub in self.hubs:
            if hub.x == x and hub.y == y:
                return True
        return False

    @staticmethod
    def _parse_metadata(id: int, hub: bool, metadata_str: str) -> Metadata:
        if not metadata_str:
            return Metadata(None, None, None, None)
        split = metadata_str.split(" ")
        key: str
        value: str
        color: Color | None = None
        max_link_capacity: int | None = None
        max_drones: int | None = None
        zone: Zone | None = None
        already_set: list[str] = []
        valid_keys: list[str] = ["color", "max_drones", "zone"]
        if not hub:
            valid_keys = ["max_link_capacity"]
        for kv in split:
            if "=" not in kv:
                raise MapParsingError(id, "metadata doesn't respect the "
                                      "format: 'key=value'")
            key, value, *rest = kv.split("=")
            if key not in valid_keys:
                raise MapParsingError(id, f"metadata key '{key}' isn't valid "
                                      f"for {"hub" if hub else "connection"} "
                                      "key")
            if len(rest) > 0:
                raise MapParsingError(id, "metadata doesn't respect the "
                                      "format: 'key=value'")
            if key not in already_set:
                already_set.append(key)
            else:
                raise MapParsingError(id, f"metadata key '{key}' is already "
                                      "set")
            match key:
                case "color":
                    color = Color.get_color(value.lower())
                    if not color:
                        raise MapParsingError(id, f"color '{value}' is not "
                                              "valid, must "
                                              f"be in {Color._member_names_}")
                case "max_link_capacity":
                    try:
                        max_link_capacity = int(value)
                    except ValueError:
                        raise MapParsingError(id, "max_link_capacity must"
                                              " be positive integer")
                    if max_link_capacity <= 0:
                        raise MapParsingError(id, "max_link_capacity must"
                                              " be positive integer")
                case "max_drones":
                    try:
                        max_drones = int(value)
                    except ValueError:
                        raise MapParsingError(id, "max_drones must"
                                              " be positive integer")
                    if max_drones <= 0:
                        raise MapParsingError(id, "max_drones must"
                                              " be positive integer")
                case "zone":
                    zone = Zone.get_zone(value.lower())
                    if not zone:
                        raise MapParsingError(id, f"zone '{value}' is not "
                                              "valid, must "
                                              f"be in {Zone._member_names_}")
                case default:
                    raise MapParsingError(id, f"metadata key '{default}' is "
                                          "not supported")
            already_set.append(key)
        return Metadata(
            zone,
            color,
            max_link_capacity,
            max_drones
        )

    def _parser(self) -> None:
        node_type: str
        node_data: str
        metadata_str: str
        first_line: bool = True
        for id, line in enumerate(self.file, start=1):
            line = line.split('#')[0].strip()
            if not line:
                continue
            if line.count(":") != 1:
                raise MapParsingError(id, "line doesn't respect the "
                                      "format: 'key: data'")
            line, metadata_str = self._extract_metadata_str(id, line)
            node_type, node_data = line.split(":")
            node_params: list[str] = node_data.strip().split()
            match node_type:
                case "nb_drones":
                    self.validate_nb_drones(id, node_params, metadata_str)
                case "start_hub":
                    self.validate_hub(id, "start_hub",
                                      node_params, metadata_str)
                case "end_hub":
                    self.validate_hub(id, "end_hub",
                                      node_params, metadata_str)
                case "hub":
                    self.validate_hub(id, "hub",
                                      node_params, metadata_str)
                case "connection":
                    self.validate_connection(id, node_params, metadata_str)
            if first_line and node_type != "nb_drones":
                raise MapParsingError(id, " first line must define the "
                                      "number of drones using "
                                      "'nb_drones: <positive_integer>'")
            first_line = False
        if self.nb_drones is None:
            raise MapParsingError(0, "missing key 'nb_drones' "
                                  "in configuration in file")
        if self.start_hub is None:
            raise MapParsingError(0, "missing key 'start_hub' "
                                  "in configuration in file")
        if self.end_hub is None:
            raise MapParsingError(0, "missing key 'end_hub' "
                                  "in configuration in file")

    def validate_nb_drones(self, id: int,
                           node_params: list[str], metadata_str: str) -> None:
        if len(node_params) != 1 or metadata_str:
            raise MapParsingError(id, "nb_drones must have only"
                                  " ONE argument without metadata")
        if self.nb_drones is None:
            try:
                self.nb_drones = int(node_params[0])
                if self.nb_drones <= 0:
                    raise Exception
            except Exception:
                raise MapParsingError(id, "nb_drones must be "
                                      "a positive integer")
        else:
            raise MapParsingError(id, "nb_drones is already set")

    def validate_hub(self, id: int, hub_type: str,
                     node_params: list[str], metadata_str: str) -> None:
        if len(node_params) != 3:
            raise MapParsingError(id, f"{hub_type} must have 3 arguments: "
                                  f"'{hub_type}: <name> <x> <y>'")
        if (hub_type == "start_hub" and self.start_hub) \
           or (hub_type == "end_hub" and self.end_hub):
            raise MapParsingError(id, f"{hub_type} is already set")
        try:
            name: str = node_params[0]
            x: int = int(node_params[1])
            y: int = int(node_params[2])
        except ValueError:
            raise MapParsingError(id, "x and y must be integers")
        if "-" in name:
            raise MapParsingError(id, "'-' in hub name is forbidden")
        if not name.isprintable():
            raise MapParsingError(id, "hub name must be printable")
        if self._get_node_from_name(name):
            raise MapParsingError(id, f"name '{name}' is taken")
        if self._are_coords_taken(x, y):
            raise MapParsingError(id, f"coords {x},{y} are already taken")

        if hub_type == "start_hub":
            self.start_hub = Node(name,
                                  x, y,
                                  self._parse_metadata(id, True, metadata_str))
            self.hubs.append(self.start_hub)
        elif hub_type == "end_hub":
            self.end_hub = Node(name,
                                x, y,
                                self._parse_metadata(id, True, metadata_str))
            self.hubs.append(self.end_hub)
        else:
            self.hubs.append(Node(name,
                             x, y,
                             self._parse_metadata(id, True, metadata_str)))

    def validate_connection(self, id: int,
                            node_params: list[str], metadata_str: str) -> None:
        if len(node_params) != 1:
            raise MapParsingError(id, "connection must have only"
                                  " ONE argument without metadata")
        connection_split: list[str] = node_params[0].split("-", 1)
        name1: str = connection_split[0]
        name2: str = connection_split[1]
        node1: Node | None = self._get_node_from_name(name1)
        node2: Node | None = self._get_node_from_name(name2)
        if not node1:
            raise MapParsingError(id, f"connection name '{name1}' must be "
                                  "in hubs")
        if not node2:
            raise MapParsingError(id, f"connection name '{name2}' must be "
                                  "in hubs")
        new_connection: Connection = Connection(
            node1,
            node2,
            self._parse_metadata(id, False, metadata_str)
        )
        if new_connection in self.connections:
            raise MapParsingError(id, f"connection between {name1} and {name2}"
                                  " already exists")
        self.connections.add(new_connection)

    def __exit__(self,
                 exc_type: type[BaseException] | None,
                 exc: BaseException | None,
                 tb: TracebackType | None) -> None:
        self.file.close()
