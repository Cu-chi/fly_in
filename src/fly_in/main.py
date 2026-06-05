"""Main module of Fly-in."""
from fly_in.map_parser import MapParsingError
from fly_in.map_categorizer import MapCategorizer
from fly_in.map_types import Map
from fly_in.visualizer import VMenu


def main() -> None:
    """Start main of Fly-in."""
    maps = MapCategorizer("maps/")
    valid_maps: dict[str, dict[str, Map]] = maps.get_valid_maps()

    if len(valid_maps) == 0:
        print("error: maps folder is empty.")
        return
    vmenu = VMenu(valid_maps)
    vmenu.run()
    return


if __name__ == "__main__":
    try:
        main()
    except MapParsingError as e:
        print(f"line {e.line}: {e.error}")
