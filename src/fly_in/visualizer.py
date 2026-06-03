import sys
import pygame
import pygame.gfxdraw
from fly_in.map_types import Node, Connection, Map
from typing import Any
from fly_in.output import Output
from fly_in.simulation import PathFinder
from enum import Enum, auto
import math


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
            self.last_scale = scale
            self.text_surface = pygame.transform.smoothscale(
                self.original_text_surface, (new_width, new_height))
            self.text_rect = self.text_surface.get_rect(center=(x, y))
        self.rect.center = (x, y)
        self.text_rect.centerx = self.rect.centerx
        self.text_rect.bottom = self.rect.top


class VConnection():
    def __init__(self, connection: Connection):
        self.connection = connection
        self.color = pygame.Color(255, 255, 255)

    def draw(self, surface: pygame.Surface, x1: int, y1: int,
             x2: int, y2: int, scale: float) -> None:
        new_width: int = max(1, int(10 * scale))
        pygame.draw.line(surface, self.color,
                         (x1, y1), (x2, y2), new_width)


class VDrone(pygame.sprite.Sprite):
    def __init__(self, position: Node | Connection, id: int,
                 font: pygame.font.Font,
                 screen_x: int, screen_y: int, *groups: Any):
        super().__init__(*groups)

        self.original_image = pygame.image.load("src/fly_in/assets/drone.png")
        self.original_image = pygame.transform.scale(self.original_image,
                                                     (96, 96))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(screen_x, screen_y))
        self.pos = position
        self.id = id
        self.last_scale = 1.0
        self.original_text_surf = font.render(str(self.id),
                                              True, (0, 0, 0))
        self.text_rect = self.original_text_surf.get_rect()
        self.text_surf = self.original_text_surf.copy()

    def draw(self, screen: pygame.Surface) -> None:
        screen.blit(self.image, self.rect)
        screen.blit(self.text_surf, self.text_rect)

    def update(self, x: int, y: int, scale: float) -> None:
        if scale != self.last_scale:
            self.last_scale = scale
            self.image = pygame.transform.scale_by(self.original_image, scale)
            self.rect = self.image.get_rect(center=(x, y))

            original_width = self.original_text_surf.get_width()
            original_height = self.original_text_surf.get_height()
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            self.last_scale = scale
            self.text_surf = pygame.transform.smoothscale(
                self.original_text_surf, (new_width, new_height))
            self.text_rect = self.text_surf.get_rect(
                center=self.rect.center)
        self.rect.center = (x, y)
        self.text_rect = self.text_surf.get_rect(
            center=(x, y))


class VExitState(Enum):
    EXIT_ALL = auto()
    SHOW_MENU = auto()
    CONTINUE = auto()


class VMenu(pygame.sprite.Sprite):
    def __init__(self, maps: dict[str, dict[str, Map]], *groups: Any):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)

        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 24)
        self.font_button = pygame.font.SysFont("Segoe UI", 16, bold=True)

        self.clock = pygame.time.Clock()
        self.show_visu = False
        self.show_menu = True

        self.categories: dict[str, dict[str, Map]] = maps

        self.selected_cat: str | None = None
        self.selected_map_name: str | None = None
        self.selected_map_data: Map | None = None

        self.show_err = ""

        super().__init__(*groups)

    def _draw_button(self, text: str, rect: pygame.Rect,
                     is_hover: bool, is_selected: bool,
                     is_action: bool = False) -> bool:

        bg_color: tuple[int, int, int] = (30, 41, 59)
        text_color: tuple[int, int, int] = (203, 213, 225)

        if is_action:
            bg_color = (16, 185, 129)
            text_color = (255, 255, 255)
        elif is_selected:
            bg_color = (14, 165, 233)
            text_color = (255, 255, 255)
        elif is_hover:
            bg_color = (56, 189, 248)
            text_color = (15, 23, 42)

        pygame.draw.rect(self.screen, bg_color, rect, border_radius=8)

        txt_surf = self.font_button.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        self.screen.blit(txt_surf, txt_rect)

        return is_hover

    def run(self) -> None:
        app_running = True

        while app_running:
            pygame.display.set_caption("Fly-in - Main Menu")

            while self.show_menu:
                screen_w, screen_h = self.screen.get_size()
                mouse_x, mouse_y = pygame.mouse.get_pos()
                mouse_clicked = False

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:
                            mouse_clicked = True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return

                self.screen.fill((15, 23, 42))

                title_surf = self.font_title.render(
                    "FLY-IN", True, (248, 250, 252))
                self.screen.blit(title_surf, (50, 50))

                sub_surf = self.font_subtitle.render(
                    "Select a map to start simulation", True, (148, 163, 184))
                self.screen.blit(sub_surf, (50, 110))

                cat_x, cat_y = 50, 200
                for cat in self.categories.keys():
                    rect = pygame.Rect(cat_x, cat_y, 250, 45)
                    hover = rect.collidepoint(mouse_x, mouse_y)

                    if hover and mouse_clicked:
                        self.selected_cat = cat
                        self.selected_map_name = None
                        self.selected_map_data = None

                    self._draw_button(cat, rect, hover,
                                      self.selected_cat == cat)
                    cat_y += 55

                map_x, map_y = 350, 200
                if self.selected_cat:
                    for name, map_data in self.categories[self.selected_cat] \
                       .items():
                        rect = pygame.Rect(map_x, map_y, 350, 45)
                        hover = rect.collidepoint(mouse_x, mouse_y)

                        if hover and mouse_clicked:
                            self.selected_map_name = name
                            self.selected_map_data = map_data

                        self._draw_button(name, rect, hover,
                                          self.selected_map_name == name)
                        map_y += 55

                if self.selected_map_data:
                    start_rect = pygame.Rect(screen_w - 300, screen_h - 120,
                                             250, 60)
                    hover = start_rect.collidepoint(mouse_x, mouse_y)

                    if hover and mouse_clicked:
                        self.show_menu = False
                        self.show_visu = True
                        self._draw_button("LOADING...", start_rect, hover,
                                          False, is_action=True)
                    else:
                        self._draw_button("START SIMULATION", start_rect,
                                          hover, False, is_action=True)

                if self.show_err:
                    err = self.font_title.render(f"[ERROR] {self.show_err}",
                                                 True, (255, 80, 80))
                    screen_rect = self.screen.get_rect()
                    err_rect = err.get_rect(center=(screen_rect.centerx, 100))
                    self.screen.blit(err, err_rect)

                pygame.display.flip()
                self.clock.tick(60)

            self.show_err = ""
            if not self.show_visu:
                break

            if self.selected_map_data:
                print(f"Starting simulation for map: {self.selected_map_name}")
                try:
                    path_finder = PathFinder(self.selected_map_data)
                    path_finder.route_all_drones()
                    output = Output(path_finder.drones_paths)
                    drones_positions = output.generate_list_of_positions()
                    output_title = f"=== {self.selected_map_name} ==="
                    print(output_title)
                    output.from_positions_print_turns(drones_positions)
                    print("=" * len(output_title))

                    visualizer = Visualizer(self.screen,
                                            self.selected_map_data,
                                            drones_positions)

                    while self.show_visu:
                        match visualizer.visualization():
                            case VExitState.EXIT_ALL:
                                self.show_menu = False
                                self.show_visu = False
                                app_running = False
                            case VExitState.SHOW_MENU:
                                self.show_menu = True
                                self.show_visu = False
                        pygame.display.flip()
                        self.clock.tick(60)
                except Exception as e:
                    self.show_err = f"{e.__class__.__name__}: {e}"
                    print(self.show_err, file=sys.stderr)
                    self.show_visu = False
                    self.show_menu = True

        pygame.quit()


class Visualizer():
    def __init__(self, screen: pygame.Surface, map: Map,
                 drones_positions: list[dict[int, Node | Connection]]) -> None:
        pygame.display.set_caption("Fly-in - Visualization")
        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 16)
        self.font_small_bold = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.screen = screen

        self.anim_speed = 0.05
        self.max_turn = len(drones_positions)
        self.paused = False

        self.set_data(map, drones_positions)
        self.running = True

    def set_data(self, map: Map,
                 drones_positions: list[dict[int, Node | Connection]]) -> None:
        self.vnodes: dict[str, VNode] = {}
        self.hubs = map.hubs
        self.connections = map.connections
        self.drones_positions = drones_positions
        self.drones_positions.insert(0, {
            id: map.start_hub for id in range(1, map.nb_drones + 1)
        })
        self.norm_val = 240
        self.scale = 1.0
        self.turn = 0
        self.cur_turn = 0.0
        self.offset_x = 0
        self.offset_y = 0
        self._center_and_fit_map()
        self.mousedown = False
        self.nb_drones = map.nb_drones
        self.end = map.end_hub

        for hub in map.hubs:
            x, y = self._normalize_pos(hub)
            self.vnodes.update({hub.name: VNode(hub, x, y, self.font)})

        self.vconnections: list[VConnection] = [
            VConnection(connection)
            for connection in map.connections
        ]
        self.vdrones: list[VDrone] = [
            VDrone(map.start_hub, id,
                   self.font_small_bold, *self._normalize_pos(map.start_hub))
            for id in range(1, map.nb_drones + 1)
        ]

        self.NEXT_TURN_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.NEXT_TURN_EVENT, 1000)

    def _normalize_pos(self, node: Node) -> tuple[int, int]:
        return (int((node.x) * self.norm_val * self.scale) + self.offset_x,
                int((node.y) * self.norm_val * self.scale) + self.offset_y)

    def _normalize_any(self,
                       node_or_conn: Node | Connection) -> tuple[int, int]:
        if isinstance(node_or_conn, Node):
            return self._normalize_pos(node_or_conn)
        elif isinstance(node_or_conn, Connection):
            x1, y1 = self._normalize_pos(node_or_conn.node1)
            x2, y2 = self._normalize_pos(node_or_conn.node2)
            return (x1 + x2) // 2, (y1 + y2) // 2

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

    def _update_drone_pos(self) -> None:
        for drone_id, vdrone in enumerate(self.vdrones, start=1):
            positions = self.drones_positions[self.turn]
            if drone_id in positions:
                vdrone.pos = positions[drone_id]

    def visualization(self) -> VExitState:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return VExitState.EXIT_ALL
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return VExitState.SHOW_MENU
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_LEFT:
                    if self.turn > 0:
                        self._update_drone_pos()
                        self.turn -= 1
                        self.cur_turn = self.turn
                if event.key == pygame.K_RIGHT:
                    if self.turn < self.max_turn:
                        self._update_drone_pos()
                        self.turn += 1
                        self.cur_turn = self.turn
                if event.key == pygame.K_r:
                    self.turn = 0
                    self.cur_turn = 0.0
                    self.paused = False
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
            if event.type == self.NEXT_TURN_EVENT and not self.paused:
                if self.turn < self.max_turn:
                    self.turn += 1
            if event.type == pygame.VIDEORESIZE:
                self._center_and_fit_map()

        progress: float = self.cur_turn - math.floor(self.cur_turn)

        self.screen.fill((15, 23, 42))

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
            dest_pos: Node | Connection | None = None
            if drone_id in positions:
                dest_pos = positions[drone_id]
                if self.cur_turn >= self.turn:
                    vdrone.pos = positions[drone_id]

            dest_x, dest_y = 0, 0
            x, y = self._normalize_any(vdrone.pos)
            if dest_pos:
                dest_x, dest_y = self._normalize_any(dest_pos)
                x, y = int(x + ((dest_x - x) * progress)), \
                    int(y + ((dest_y - y) * progress))
            vdrone.update(x, y, self.scale)
            vdrone.draw(self.screen)

        if not self.paused:
            self.cur_turn += self.anim_speed
            self.cur_turn = min(self.turn, self.cur_turn)

        bg_surf = pygame.Surface((400, 250), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 100))
        self.screen.blit(bg_surf, (0, 0))

        title = self.font_title.render("Simulation", True, (255, 255, 255))
        turn = self.font_small.render(f"Turn: {self.turn}/{self.max_turn}",
                                      True, (255, 255, 255))
        arrived = self.font_small.render(
            f"Drones arrived: {
                len([1 for d in self.vdrones if d.pos == self.end])
            }/{self.nb_drones}",
            True, (255, 255, 255))
        state_title = self.font_small.render("State:", True, (255, 255, 255))
        if self.paused:
            state = self.font_small.render("PAUSED", True, (255, 120, 120))
        elif self.cur_turn < self.max_turn:
            state = self.font_small.render("RUNNING", True, (255, 255, 40))
        else:
            state = self.font_small.render("ENDED", True, (120, 255, 120))
        self.screen.blit(turn, (10, 80))
        self.screen.blit(state_title, (10, 100))
        self.screen.blit(state, (55, 100))
        self.screen.blit(arrived, (10, 120))

        desc = [
            "SPACE: pause",
            "ESC: back to main menu",
            "R: restart simulation",
            "LEFT/RIGHT ARROW: increase/decrease turn"
        ]
        desc_y: int = 140
        for desc_str in desc:
            desc_y += 20
            desc_surf = self.font_small.render(desc_str, True, (150, 255, 255))
            self.screen.blit(desc_surf, (10, desc_y))

        self.screen.blit(title, (60, 20))

        return VExitState.CONTINUE
