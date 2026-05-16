from fly_in.map import Map
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
        self.lc: int = 0

    def __enter__(self) -> 'MapParser':
        self.file = open(self.filename, "r")
        self._parser()
        return self

    def readline(self):
        self.lc += 1
        return self.file.readline().strip()

    def _parser(self) -> None:
        line: str = self.readline()
        node_type: str
        node_data: str
        first_line: bool = True
        while line:
            if line.startswith("#") or line.isspace():
                line = self.readline()
            if line.count(":") != 1:
                raise MapParsingError(self.lc, "line doesn't respect the "
                                      "format: 'key: data'")
            node_type, node_data = line.split(":")
            node_params: list[str] = node_data.strip().split(" ")
            match node_type:
                case "nb_drones":
                    self.validate_nb_drones(node_params)
            if first_line and node_type != "nb_drones":
                first_line = False
                raise MapParsingError(self.lc, " first line must define the "
                                      "number of drones using "
                                      "'nb_drones: <positive_integer>'")
            line = self.readline()
        if self.nb_drones is None:
            raise MapParsingError(self.lc, "missing configuration in file")

    def validate_nb_drones(self, node_params: list[str]):
        if len(node_params) != 1:
            raise MapParsingError(self.lc, "nb_drones must have only"
                                  " ONE argument")
        if self.nb_drones is None:
            try:
                self.nb_drones = int(node_params[0])
            except Exception:
                raise MapParsingError(self.lc, "nb_drones must be "
                                      "an integer")
        else:
            raise MapParsingError(self.lc, "nb_drones is already set")

    def __exit__(self, exc_type, exc, tb) -> None:
        self.file.close()
