"""Module for categorization of the maps of Fly-in."""
from fly_in.map_parser import MapParser, MapParsingError
from fly_in.map_types import Map
from pathlib import Path
import glob
import sys


class MapCategorizer():
    """A class representing a MapCategorizer."""

    def __init__(self, maps_folder: str) -> None:
        """Initialize a MapCategorizer object.

        Args:
            maps_folder (str): folder name
        """
        self.maps_folder = maps_folder

    def get_valid_maps(self) -> dict[str, dict[str, Map]]:
        """Get all valid maps in the maps_folder folder.

        Returns:
            dict[str, dict[str, Map]]: structured dict with each Map associed
        """
        map_paths = glob.glob(self.maps_folder + "/**/*.txt")
        map_dict: dict[str, dict[str, Map]] = {}

        for map_path in map_paths:
            print(f"\nLoading map: {map_path}")
            try:
                with MapParser(map_path) as map:
                    path = Path(map_path)
                    cat_dict = map_dict.get(path.parent.name)
                    if not cat_dict:
                        map_dict.update({path.parent.name: {}})
                        cat_dict = map_dict[path.parent.name]
                    cat_dict.update({path.stem: map})
            except MapParsingError as e:
                print(f"line {e.line}: {e.error}", file=sys.stderr)
        return map_dict
