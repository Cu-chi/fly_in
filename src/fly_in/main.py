from fly_in.map import Map
from fly_in.map_parser import MapParser, MapParsingError

def main() -> None:
    with MapParser("maps/test.txt") as map_parse:
        print(map_parse.hubs)
    # map: Map = map_parser.map


if __name__ == "__main__":
    try:
        main()
    except MapParsingError as e:
        print(f"line {e.line}: {e.error}")
