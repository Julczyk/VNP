from world.world import World
from world.tile import WaterTile
import arcade
from config import ResourceType

# =====================
# KONFIGURACJA WIDOKU
# =====================

TILE_SIZE = 10
SCREEN_MARGIN = 20

LAND_COLOR = arcade.color.DARK_SPRING_GREEN

RESOURCE_COLORS = {
    ResourceType.RAW_ORE: arcade.color.BROWN,
    ResourceType.COAL: arcade.color.DARK_BROWN,
    ResourceType.IRON: arcade.color.GRAY,
    ResourceType.GOLD: arcade.color.GOLD,
    ResourceType.URANIUM: arcade.color.LIME_GREEN,

    ResourceType.PROCESSED_METAL: arcade.color.SILVER,
    ResourceType.ENERGY: arcade.color.YELLOW,

    ResourceType.PART_ENGINE: arcade.color.RED,
    ResourceType.PART_SCANNER: arcade.color.BLUE,
}



# =====================
# OKNO WIZUALIZACJI
# =====================

class WorldView(arcade.Window):
    def __init__(self, world: World):
        self.world = world
        self.tick = 0
        self.paused = False
        self.selected_automaton = None

        width = world.width * TILE_SIZE + SCREEN_MARGIN * 2
        height = world.height * TILE_SIZE + SCREEN_MARGIN * 2

        self.info_box_x = 10 
        self.info_box_y = height - 70
        self.close_btn_size = 20 

        super().__init__(width, height, "World visualization")
        arcade.set_background_color(arcade.color.BLACK)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.selected_automaton is not None:
            close_x = self.info_box_x + 200
            close_y = self.info_box_y + 10
            btn_size = self.close_btn_size

            if (close_x - btn_size / 2 <= x <= close_x + btn_size / 2 and
                    close_y - btn_size / 2 <= y <= close_y + btn_size / 2):
                self.selected_automaton = None
                return 

        for automaton in self.world.automata:
            ax, ay = automaton.position
            draw_x = SCREEN_MARGIN + ax * TILE_SIZE + TILE_SIZE / 2
            draw_y = SCREEN_MARGIN + ay * TILE_SIZE + TILE_SIZE / 2

            dist = ((x - draw_x) ** 2 + (y - draw_y) ** 2) ** 0.5

            if dist <= TILE_SIZE / 2:
                self.selected_automaton = automaton
                break
        else:
            self.selected_automaton = None


    def on_draw(self):
        self.clear()

        # ===== MAPA =====
        for y in range(self.world.height):
            for x in range(self.world.width):
                tile = self.world.map[y, x]

                draw_x = SCREEN_MARGIN + x * TILE_SIZE
                draw_y = SCREEN_MARGIN + y * TILE_SIZE

                # WODA
                if isinstance(tile, WaterTile):
                    depth = min(tile.depth, 1.0)
                    blue = int(120 + 100 * depth)
                    color = (0, 0, blue)

                # LĄD
                else:
                    color = LAND_COLOR
                    if tile.materials:
                        res = max(tile.materials.items(), key=lambda x: x[1])[0]
                        color = RESOURCE_COLORS.get(res, LAND_COLOR)

                arcade.draw_lbwh_rectangle_filled(
                    draw_x,
                    draw_y,
                    TILE_SIZE,
                    TILE_SIZE,
                    color
                )

        # ===== WRAKI =====
        for x, y, resources in self.world.wrecks:
            draw_x = SCREEN_MARGIN + x * TILE_SIZE + TILE_SIZE / 2
            draw_y = SCREEN_MARGIN + y * TILE_SIZE + TILE_SIZE / 2

            arcade.draw_lbwh_rectangle_filled(
                draw_x - TILE_SIZE // 4,
                draw_y - TILE_SIZE // 4,
                TILE_SIZE // 2,
                TILE_SIZE // 2,
                arcade.color.BROWN
            )

        # ===== AUTOMATY =====
        for automaton in self.world.automata:
            x, y = automaton.position

            draw_x = SCREEN_MARGIN + x * TILE_SIZE + TILE_SIZE / 2
            draw_y = SCREEN_MARGIN + y * TILE_SIZE + TILE_SIZE / 2

            # kolor zależny od energii
            energy_ratio = automaton.energy / automaton.max_energy
            energy_ratio = max(0.0, min(1.0, energy_ratio))

            color = (
                int(255 * (1 - energy_ratio)),
                int(255 * energy_ratio),
                0
            )

            # nowo narodzony automat
            if self.world.tick - automaton.birth_tick < 20:
                color = arcade.color.CYAN

            # >>> PODŚWIETLENIE ZBIERANIA <<<
            if hasattr(automaton, "last_collected_tick"):
                if self.world.tick - automaton.last_collected_tick < 5:
                    color = arcade.color.YELLOW

            arcade.draw_circle_filled(
                draw_x,
                draw_y,
                TILE_SIZE // 2,
                color
            )

        # ===== HUD =====
        arcade.draw_text(
            f"Tick: {self.world.tick} {'(PAUSED)' if self.paused else ''}",
            10,
            self.height - 25,
            arcade.color.WHITE,
            14
        )

        # ===== AUTOMATA INFO =====

        if self.selected_automaton is not None:
            a = self.selected_automaton
            info_x = self.info_box_x
            info_y = self.info_box_y
            btn_size = self.close_btn_size

            def wrap_text(text, max_len=30):
                words = text.split(", ")
                lines = []
                current_line = ""
                for w in words:
                    if len(current_line) + len(w) + 2 <= max_len:
                        current_line += (", " if current_line else "") + w
                    else:
                        lines.append(current_line)
                        current_line = w
                if current_line:
                    lines.append(current_line)
                return lines

            line_height = 18
            font_size = 12

            fixed_lines_count = 5

            # Storage
            storage_lines_count = 0
            storage_parts = a.get_storage_parts()
            wrapped_storage = []
            if storage_parts:
                storage_contents = []
                for s in storage_parts:
                    for res_type, amt in s.contents.items():
                        storage_contents.append(f"{res_type.name}: {amt:.6f}")
                storage_str = ', '.join(storage_contents)
                wrapped_storage = wrap_text(storage_str)
                storage_lines_count = len(wrapped_storage)

            # Calculate total lines:
            total_lines = fixed_lines_count + 1 
            if storage_parts:
                total_lines += 1 + storage_lines_count

            # Box
            bg_width = 215
            padding_top = 20
            padding_bottom = 20
            bg_height = total_lines * line_height + padding_top + padding_bottom

            arcade.draw_lbwh_rectangle_filled(
                info_x - 5,
                info_y - bg_height + padding_top,
                bg_width,
                bg_height,
                arcade.color.DARK_SLATE_GRAY
            )

            # Basic info
            arcade.draw_text(f"Automaton @ {a.position}", info_x, info_y, arcade.color.WHITE, font_size)
            arcade.draw_text(f"Energy: {a.energy:.1f} / {a.max_energy}", info_x, info_y - line_height, arcade.color.WHITE, font_size)
            arcade.draw_text(f"Alive: {'Yes' if a.alive else 'No'}", info_x, info_y - 2*line_height, arcade.color.WHITE, font_size)
            arcade.draw_text(f"Age: {self.world.tick - a.birth_tick}", info_x, info_y - 3*line_height, arcade.color.WHITE, font_size)
            arcade.draw_text(f"Children count: {a.children_count}", info_x, info_y - 4*line_height, arcade.color.WHITE, font_size)

            if storage_parts:
                storage_start_y = info_y - fixed_lines_count * line_height
                arcade.draw_text("Storage:", info_x, storage_start_y, arcade.color.WHITE, 12)
                for i, line in enumerate(wrapped_storage):
                    arcade.draw_text(line, info_x, storage_start_y - (1 + i) * line_height, arcade.color.WHITE, 12)

            # Close button 
            close_x = info_x + 200
            close_y = info_y + 10
            arcade.draw_lbwh_rectangle_filled(close_x - btn_size / 2, close_y - btn_size / 2, btn_size, btn_size, arcade.color.RED)
            line_offset = btn_size / 4
            arcade.draw_line(close_x - line_offset, close_y - line_offset,
                            close_x + line_offset, close_y + line_offset, arcade.color.WHITE, 2)
            arcade.draw_line(close_x - line_offset, close_y + line_offset,
                            close_x + line_offset, close_y - line_offset, arcade.color.WHITE, 2)


        arcade.draw_text(
            f"Automata: {len(self.world.automata)}",
            10,
            self.height - 45,
            arcade.color.WHITE,
            14
        )

    def on_update(self, delta_time: float):
        if not self.paused:
            if self.tick % 5 == 0:      # <-- REGULUJ TUTAJ predkosc symulacji
                self.world.update()
            self.tick += 1

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            self.paused = not self.paused


# =====================
# START SYMULACJI
# =====================

if __name__ == "__main__":
    from automaton import Automaton
    from parts import (
        Engine, Scanner, Storage,
        Smelter, Assembler,
        Collector, PowerGenerator
    )
    from config import FunctionID, ResourceType

    program = [
        (FunctionID.SCAN.value, []),
        (FunctionID.MOVE.value, ["MEM0", "MEM1"]),  # idź aż do celu
        (FunctionID.COLLECT.value, [5]),
        (FunctionID.IDLE.value, []),
    ]

    genome = [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.0),
        (Collector, 1.0),
        (Smelter, 1.0),
        (Assembler, 1.0),
        (PowerGenerator, 1.0),
    ]

    world = World(80, 80, seed=42)

    automaton = Automaton(
        program_code=program,
        parts_genome=genome,
        world=world,
        position=(15, 15)
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()

