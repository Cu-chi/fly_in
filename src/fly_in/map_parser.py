from fly_in.map import Node, Metadata, Color, Zone
from typing import Any


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
        self.connections: set[tuple[Node, Node]] = set()

    def __enter__(self) -> 'MapParser':
        self.file = open(self.filename, "r")
        self._parser()
        return self

    @staticmethod
    def _extract_metadata_str(line: str) -> tuple[str, str]:
        """Extract metadata from the line and return
        line without metadata and metadata without brackets

        Args:
            line (str): the line

        Returns:
            tuple[str, str]: first is the line without metadata,
            second is only the metadata without brackets
        """
        opening = line.find("[")
        closing = line.find("]")
        if opening == -1 or closing == -1:
            return line, ""
        return line[:opening], line[opening + 1:closing].strip()

    def _is_name_taken(self, name: str) -> bool:
        for hub in self.hubs:
            if hub.name == name:
                return True
        return False

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
    def _parse_metadata(id: int, metadata_str: str) -> Metadata:
        split = metadata_str.split(" ")
        metadata = Metadata(Zone.NORMAL, None, 1, 1)
        key: str
        value: str
        for kv in split:
            key, value = kv.split("=")
            match key:
                case "color":
                    color: Color | None = Color.get_color(value.lower())
                    if not color:
                        raise MapParsingError(id, f"color '{value}' is not "
                                              "valid, must "
                                              f"be in {Color._member_names_}")
                    metadata.color = color
                case "max_link_capacity":
                    metadata.max_link_capacity = int(value)
                    if metadata.max_link_capacity < 0:
                        raise MapParsingError(id, "max_link_capacity must"
                                              " be positive integer")
                case "max_drones":
                    metadata.max_drones = int(value)
                    if metadata.max_drones < 0:
                        raise MapParsingError(id, "max_drones must"
                                              " be positive integer")
                case "zone":
                    zone: Zone | None = Zone.get_zone(value.lower())
                    if not zone:
                        raise MapParsingError(id, f"zone '{value}' is not "
                                              "valid, must "
                                              f"be in {Zone._member_names_}")
                    metadata.zone = zone
                case default:
                    raise MapParsingError(id, f"metadata key '{default}' is "
                                          "not supported")
        return metadata

    def _parser(self) -> None:
        node_type: str
        node_data: str
        metadata_str: str
        first_line: bool = True
        for id, line in enumerate(self.file, start=1):
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.count(":") != 1:
                raise MapParsingError(id, "line doesn't respect the "
                                      "format: 'key: data'")
            line, metadata_str = self._extract_metadata_str(line)
            node_type, node_data = line.split(":")
            node_params: list[str] = node_data.strip().split(" ")
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
                if self.nb_drones < 0:
                    raise Exception
            except Exception:
                raise MapParsingError(id, "nb_drones must be "
                                      "a positive integer")
        else:
            raise MapParsingError(id, "nb_drones is already set")

    def validate_hub(self, id: int, hub_type: str,
                     node_params: list[str], metadata_str: str) -> None:
        if len(node_params) != 3:
            raise MapParsingError(id, f"{hub_type} must have "
                                  f" 3 arguments: '{hub_type}: <name> <x> <y>'")
        if (hub_type == "start_hub" and self.start_hub) \
           or (hub_type == "end_hub" and self.end_hub):
            raise MapParsingError(id, f"{hub_type} is already set")
        try:
            name: str = node_params[0]
            x: int = int(node_params[1])
            y: int = int(node_params[2])
        except ValueError:
            raise MapParsingError(id, "x and y must be integers")
        if not name.isalnum():
            raise MapParsingError(id, "hub name must be alpha-numerical")
        if self._is_name_taken(name):
            raise MapParsingError(id, f"name '{name}' is taken")
        if self._are_coords_taken(x, y):
            raise MapParsingError(id, f"coords {x},{y} are already taken")

        if hub_type == "start_hub":
            self.start_hub = Node(name,
                                  x, y,
                                  self._parse_metadata(id, metadata_str))
            self.hubs.append(self.start_hub)
        elif hub_type == "end_hub":
            self.end_hub = Node(name,
                                x, y,
                                self._parse_metadata(id, metadata_str))
            self.hubs.append(self.end_hub)
        else:
            self.hubs.append(Node(name,
                             x, y,
                             self._parse_metadata(id, metadata_str)))

    def __exit__(self, exc_type, exc, tb) -> None:
        self.file.close()
