from fly_in.map_parser import MapParser, MapParsingError, MapFolder
from fly_in.map_types import Map
from fly_in.visualizer import Visualizer, VMenu
from fly_in.simulation import PathFinder
from fly_in.output import Output


def main() -> None:
    list_maps = [
        # "maps/easy/01_linear_path.txt",
        # "maps/easy/02_simple_fork.txt",
        # "maps/easy/03_basic_capacity.txt",

        # "maps/medium/01_dead_end_trap.txt",
        # "maps/medium/02_circular_loop.txt",
        # "maps/medium/03_priority_puzzle.txt",

        # "maps/hard/01_maze_nightmare.txt",
        # "maps/hard/02_capacity_hell.txt",
        # "maps/hard/03_ultimate_challenge.txt",

        "maps/challenger/01_the_impossible_dream.txt",
    ]
    maps = MapFolder("maps/")
    valid_maps: dict[str, Map] = maps.get_valid_maps()
    vmenu = VMenu(valid_maps)
    vmenu.run()
    return
    # for path in list_maps:
    #     with MapParser(path) as map:
    #         path_finder = PathFinder(map)
    #         path_finder.route_all_drones()
    #         output = Output(path_finder.drones_paths)
    #         drones_positions = output.generate_list_of_positions()
    #         print(drones_positions)
    #         output.from_positions_print_turns(drones_positions)

    #         print(f"{path}: {len(drones_positions)}")
    #         visualizer = Visualizer(map, drones_positions)
    #         visualizer.run()
    # with MapParser("maps/challenger/01_the_impossible_dream.txt") as map:
    #     path_finder = PathFinder(map)
    #     path_finder.route_all_drones()
    #     output = Output(path_finder.drones_paths)
    #     drones_positions = output.generate_list_of_positions()
    #     output.from_positions_print_turns(drones_positions)
    #     print("nb turns ", len(drones_positions))
    #     visualizer = Visualizer(map, drones_positions)
    #     visualizer.run()


if __name__ == "__main__":
    try:
        main()
    except MapParsingError as e:
        print(f"line {e.line}: {e.error}")
