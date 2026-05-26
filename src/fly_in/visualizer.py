import pygame
import pygame.gfxdraw
from fly_in.map_parser import Map
from fly_in.map_types import Node, Connection
from typing import Any


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
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))

        center: int = size // 2
        pygame.gfxdraw.aacircle(self.image, center, center,
                                self.radius, self.color)
        pygame.gfxdraw.filled_circle(self.image, center, center,
                                     self.radius, self.color)

        self.rect = self.image.get_rect(center=(screen_x, screen_y))
        self.text_surface = font.render(node.name,
                                        True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect()

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def update(self, x: int, y: int) -> None:
        self.rect.center = (x, y)
        self.text_rect.centerx = self.rect.centerx
        self.text_rect.bottom = self.rect.top


class VConnection(pygame.sprite.Sprite):
    def __init__(self, connection: Connection,
                 font: pygame.font.Font, *groups: Any):
        super().__init__(*groups)
        self.connection = connection

        self.color = pygame.Color(255, 255, 255)
        self.font = font
        self.description = "0 drones"
        self.text_surface = font.render(self.description,
                                        True, (255, 255, 255))
        self.text_rect = self.text_surface.get_rect()
        self.mid_line: tuple[int, int] = (0, 0)

    def update_text(self, text: str) -> None:
        self.description = text
        self.text_surface = self.font.render(self.description, True,
                                             (255, 255, 255))
        self.text_rect = self.text_surface.get_rect(center=self.mid_line)

    def draw(self, surface: pygame.Surface, x1: int, y1: int,
             x2: int, y2: int, scale: float) -> None:
        new_width: int = max(1, int(1 * scale))
        self.mid_line = ((x1 + x2) // 2, (y1 + y2) // 2)
        self.text_rect.center = self.mid_line
        pygame.draw.line(surface, self.color,
                         (x1, y1), (x2, y2), new_width)
        surface.blit(self.text_surface, self.text_rect)


class VDrone(pygame.sprite.Sprite):
    def __init__(self, position: Node | Connection,
                 screen_x: int, screen_y: int, *groups: Any):
        super().__init__(*groups)

        self.image = pygame.image.load("src/fly_in/assets/drone.png")
        self.image = pygame.transform.scale(self.image, (64, 64))
        self.rect = self.image.get_rect(center=(screen_x, screen_y))
        self.position = position

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)

    def update(self, x: int, y: int) -> None:
        self.rect.center = (x, y)


class Visualizer():
    def __init__(self, map: Map,
                 drones_positions: list[dict[int, Node | Connection]]) -> None:
        pygame.init()
        self.scale = 1.0
        video_info: pygame.display._VidInfo = pygame.display.Info()
        pygame.display.set_caption("fly-in visualizer")
        self.screen = pygame.display.set_mode(
            (video_info.current_w // 2, video_info.current_h // 2),
            pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 10)
        self.vnodes: dict[str, VNode] = {}
        self.offset_x = 0
        self.offset_y = 0
        for hub in map.hubs:
            x, y = self._normalize_pos(hub)
            self.vnodes.update({hub.name: VNode(hub, x, y, self.font)})
        self.vconnections: list[VConnection] = [
            VConnection(connection, self.font_small)
            for connection in map.connections
        ]

        self.vdrones: list[VDrone] = [
            VDrone(map.start_hub, *self._normalize_pos(map.start_hub))
            for _ in range(map.nb_drones)
        ]
        self.hubs = map.hubs
        self.connections = map.connections
        self.drones_positions = drones_positions
        self.running = True

        self.NEXT_TURN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.NEXT_TURN_EVENT,
                              500,
                              len(self.drones_positions) - 1)
        self.turn = 0

    def _normalize_pos(self, node: Node) -> tuple[int, int]:
        return (int((node.x) * 240 * self.scale) + self.offset_x,
                int((node.y) * 240 * self.scale) + self.offset_y)

    def run(self) -> None:
        mousedown = False
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEWHEEL:
                    scale_factor: int = event.y * 0.1
                    if 0 < self.scale + scale_factor < 100:
                        self.scale += scale_factor
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mousedown = True
                if event.type == pygame.MOUSEBUTTONUP:
                    mousedown = False
                if event.type == pygame.MOUSEMOTION and mousedown:
                    self.offset_x += event.rel[0]
                    self.offset_y += event.rel[1]
                if event.type == self.NEXT_TURN_EVENT:
                    self.turn += 1

            self.screen.fill("gray")

            for vconnection in self.vconnections:
                x1, y1 = self.\
                    vnodes[vconnection.connection.node1.name].rect.center
                x2, y2 = self.\
                    vnodes[vconnection.connection.node2.name].rect.center
                vconnection.draw(self.screen, x1, y1, x2, y2, self.scale)

            for vnode in self.vnodes.values():
                x, y = self._normalize_pos(vnode.node)
                vnode.update(x, y)
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
                vdrone.update(x, y)
                vdrone.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
