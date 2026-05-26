from fly_in.map_parser import MapParser, MapParsingError
from fly_in.visualizer import Visualizer
from fly_in.simulation import PathFinder
from fly_in.output import Output


def main() -> None:
    with MapParser("maps/challenger/01_the_impossible_dream.txt") as map:
        path_finder = PathFinder(map)
        path_finder.route_all_drones()
        output = Output(path_finder.drones_paths)
        drones_positions = output.generate_list_of_positions()
        output.from_positions_print_turns(drones_positions)
        visualizer = Visualizer(map, drones_positions)
        visualizer.run()


if __name__ == "__main__":
    try:
        main()
    except MapParsingError as e:
        print(f"line {e.line}: {e.error}")
