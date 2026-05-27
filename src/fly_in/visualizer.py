import pygame
import pygame.gfxdraw
from fly_in.map_parser import Map
from fly_in.map_types import Node, Connection
from typing import Any
from fly_in.output import Output
from fly_in.simulation import PathFinder
from enum import Enum, auto


class VNode(pygame.sprite.Sprite):
    def __init__(self, node: Node,
                 screen_x: int, screen_y: int,
                 font: pygame.font.Font, *groups: Any):
        super().__init__(*groups)

        self.node = node
        self.radius = 64

        try:
            if node.metadata.color:
                self.color = pygame.Color(node.metadata.color.lower())
            else:
                self.color = pygame.Color(255, 255, 255)
        except ValueError:
            self.color = pygame.Color(255, 255, 255)

        padding: int = 4
        size: int = self.radius * 2 + padding
        self.original_image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.original_image.fill((0, 0, 0, 0))

        center: int = size // 2
        pygame.gfxdraw.aacircle(self.original_image, center, center,
                                self.radius, self.color)
        pygame.gfxdraw.filled_circle(self.original_image, center, center,
                                     self.radius, self.color)

        self.original_text_surface = font.render(node.name,
                                                 True, (255, 255, 255))

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(screen_x, screen_y))
        self.text_surface = self.original_text_surface.copy()
        self.text_rect = self.text_surface.get_rect()
        self.last_scale = 1.0

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def update(self, x: int, y: int, scale: float) -> None:
        if scale != self.last_scale:
            original_size = self.original_image.get_width()
            new_size = int(original_size * scale)
            new_size = max(1, new_size)
            self.last_scale = scale
            self.image = pygame.transform.smoothscale(self.original_image,
                                                      (new_size, new_size))
            self.rect = self.image.get_rect(center=(x, y))

            original_width = self.original_text_surface.get_width()
            original_height = self.original_text_surface.get_height()
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            new_size_w = max(1, new_width)
            new_size_h = max(1, new_height)
            self.last_scale = scale
            self.text_surface = pygame.transform.smoothscale(
                self.original_text_surface, (new_size_w, new_size_h))
            self.text_rect = self.text_surface.get_rect(center=(x, y))
        self.rect.center = (x, y)
        self.text_rect.centerx = self.rect.centerx
        self.text_rect.bottom = self.rect.top


class VConnection(pygame.sprite.Sprite):
    def __init__(self, connection: Connection, *groups: Any):
        super().__init__(*groups)
        self.connection = connection
        self.color = pygame.Color(255, 255, 255)

    def draw(self, surface: pygame.Surface, x1: int, y1: int,
             x2: int, y2: int, scale: float) -> None:
        new_width: int = max(1, int(10 * scale))
        pygame.draw.line(surface, self.color,
                         (x1, y1), (x2, y2), new_width)


class VDrone(pygame.sprite.Sprite):
    def __init__(self, position: Node | Connection,
                 screen_x: int, screen_y: int, *groups: Any):
        super().__init__(*groups)

        self.original_image = pygame.image.load("src/fly_in/assets/drone.png")
        self.original_image = pygame.transform.scale(self.original_image,
                                                     (96, 96))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(screen_x, screen_y))
        self.position = position
        self.last_scale = 1.0

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)

    def update(self, x: int, y: int, scale: float) -> None:
        if scale != self.last_scale:
            self.last_scale = scale
            self.image = pygame.transform.scale_by(self.original_image, scale)
            self.rect = self.image.get_rect(center=(x, y))
        self.rect.center = (x, y)


class VExitState(Enum):
    EXIT_ALL = auto()
    SHOW_MENU = auto()
    CONTINUE = auto()


class VMenu(pygame.sprite.Sprite):
    def __init__(self, maps: dict[str, Map], *groups):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (0, 0),
            pygame.RESIZABLE)

        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 10)

        self.clock = pygame.time.Clock()

        self.show_visu = False
        self.show_menu = True

        self.maps = maps

        super().__init__(*groups)

    def run(self) -> None:
        while True:
            for map in self.maps.values():
                selected = map
                break
            pygame.display.set_caption("Fly-in - Menu")
            while self.show_menu:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return VExitState.EXIT_ALL
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.show_menu = False
                        if event.key == pygame.K_SPACE:
                            self.show_menu = False
                            self.show_visu = True
                            break
                pygame.display.flip()
                self.clock.tick(60)

            if not self.show_visu:
                break

            path_finder = PathFinder(map)
            path_finder.route_all_drones()
            output = Output(path_finder.drones_paths)
            drones_positions = output.generate_list_of_positions()
            visualizer = Visualizer(self.screen, selected, drones_positions)

            while self.show_visu:
                match visualizer.visualization():
                    case VExitState.EXIT_ALL:
                        self.show_menu = False
                        self.show_visu = False
                    case VExitState.SHOW_MENU:
                        self.show_menu = True
                        self.show_visu = False
                pygame.display.flip()
                self.clock.tick(60)
            if not self.show_menu:
                break
        pygame.quit()


class Visualizer():
    def __init__(self, screen: pygame.Surface, map: Map,
                 drones_positions: list[dict[int, Node | Connection]]) -> None:
        pygame.display.set_caption("Fly-in - Visualization")
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 10)
        self.screen = screen

        self.set_data(map, drones_positions)
        self.running = True

    def set_data(self, map: Map,
                 drones_positions: list[dict[int, Node | Connection]]) -> None:
        self.vnodes: dict[str, VNode] = {}
        self.hubs = map.hubs
        self.connections = map.connections
        self.drones_positions = drones_positions
        self.norm_val = 240
        self.scale = 1.0
        self.turn = 0
        self.offset_x = 0
        self.offset_y = 0
        self._center_and_fit_map()
        self.mousedown = False

        for hub in map.hubs:
            x, y = self._normalize_pos(hub)
            self.vnodes.update({hub.name: VNode(hub, x, y, self.font)})

        self.vconnections: list[VConnection] = [
            VConnection(connection)
            for connection in map.connections
        ]
        self.vdrones: list[VDrone] = [
            VDrone(map.start_hub, *self._normalize_pos(map.start_hub))
            for _ in range(map.nb_drones)
        ]

        self.NEXT_TURN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.NEXT_TURN_EVENT,
                              500,
                              len(self.drones_positions) - 1)

    def _normalize_pos(self, node: Node) -> tuple[int, int]:
        return (int((node.x) * self.norm_val * self.scale) + self.offset_x,
                int((node.y) * self.norm_val * self.scale) + self.offset_y)

    def _center_and_fit_map(self) -> None:
        if not self.hubs:
            return

        min_x = min(hub.x for hub in self.hubs)
        max_x = max(hub.x for hub in self.hubs)
        min_y = min(hub.y for hub in self.hubs)
        max_y = max(hub.y for hub in self.hubs)

        map_width = max_x - min_x
        map_height = max_y - min_y

        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0

        screen_w, screen_h = self.screen.get_size()
        padding = 100

        width_scale = (screen_w - padding) / (map_width * self.norm_val) \
            if map_width > 0 else 1.0
        height_scale = (screen_h - padding) / (map_height * self.norm_val) \
            if map_height > 0 else 1.0

        self.scale = min(width_scale, height_scale)

        self.scale = min(self.scale, 2.0)

        if self.scale < 0.1:
            self.scale = 0.1

        self.offset_x = (screen_w // 2) - int(center_x
                                              * self.norm_val * self.scale)
        self.offset_y = (screen_h // 2) - int(center_y
                                              * self.norm_val * self.scale)

    def visualization(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return VExitState.EXIT_ALL
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return VExitState.SHOW_MENU
            if event.type == pygame.MOUSEWHEEL:
                scale_factor: int = event.y * 0.1
                if 0.1 < self.scale + scale_factor < 2.0:
                    self.scale += scale_factor
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mousedown = True
            if event.type == pygame.MOUSEBUTTONUP:
                self.mousedown = False
            if event.type == pygame.MOUSEMOTION and self.mousedown:
                self.offset_x += event.rel[0]
                self.offset_y += event.rel[1]
            if event.type == self.NEXT_TURN_EVENT:
                self.turn += 1
            if event.type == pygame.VIDEORESIZE:
                self._center_and_fit_map()

        self.screen.fill("#211e69")

        for vconnection in self.vconnections:
            x1, y1 = self.\
                vnodes[vconnection.connection.node1.name].rect.center
            x2, y2 = self.\
                vnodes[vconnection.connection.node2.name].rect.center
            vconnection.draw(self.screen, x1, y1, x2, y2, self.scale)

        for vnode in self.vnodes.values():
            x, y = self._normalize_pos(vnode.node)
            vnode.update(x, y, self.scale)
            vnode.draw(self.screen)

        for drone_id, vdrone in enumerate(self.vdrones, start=1):
            positions = self.drones_positions[self.turn]
            if drone_id in positions:
                vdrone.position = positions[drone_id]
            if isinstance(vdrone.position, Node):
                x, y = self._normalize_pos(vdrone.position)
            elif isinstance(vdrone.position, Connection):
                x1, y1 = self._normalize_pos(vdrone.position.node1)
                x2, y2 = self._normalize_pos(vdrone.position.node2)
                x, y = (x1 + x2) // 2, (y1 + y2) // 2
            vdrone.update(x, y, self.scale)
            vdrone.draw(self.screen)
        return VExitState.CONTINUE
