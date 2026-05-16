from fly_in.map_parser import MapParser, MapParsingError
import pytest
import pathlib


def test_empty(tmp_path: pathlib.Path):
    tmp = tmp_path / "empty.txt"
    tmp.touch()
    with pytest.raises(MapParsingError):
        with MapParser(str(tmp)):
            pass


def test_valide_first_line(tmp_path: pathlib.Path):
    tmp = tmp_path / "map.txt"
    tmp.write_text("""
# comment
nb_drones: 10

start_hub: start 0 0
""")
    with MapParser(str(tmp)) as map_parse:
        assert map_parse.nb_drones == 10
