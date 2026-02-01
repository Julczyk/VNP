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

        width = world.width * TILE_SIZE + SCREEN_MARGIN * 2
        height = world.height * TILE_SIZE + SCREEN_MARGIN * 2

        super().__init__(width, height, "World visualization")
        arcade.set_background_color(arcade.color.BLACK)

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
            f"Tick: {self.tick}",
            10,
            self.height - 25,
            arcade.color.WHITE,
            14
        )

        arcade.draw_text(
            f"Automata: {len(self.world.automata)}",
            10,
            self.height - 45,
            arcade.color.WHITE,
            14
        )

    def on_update(self, delta_time: float):
        if self.tick % 5 == 0:      # <-- REGULUJ TUTAJ predkosc symulacji
            self.world.update()
        self.tick += 1


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
    from srapl_interpreter import setup_logging
    import logging

    # Włącz logowanie interpretera (opcjonalne - zakomentuj dla cichej pracy)
    # setup_logging(logging.DEBUG)

    # Program SRAPL - skanuj, idź do zasobu, zbieraj, odpoczywaj
    srapl_program = '''
$PARTS:
1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0;

$PROGRAMM
# Główna pętla automatu: skanuj -> jedź -> zbieraj -> odpoczywaj

# Skanuj otoczenie w poszukiwaniu zasobów
f_2(1.0, 1.0);
'''

    # Alternatywny, bardziej zaawansowany program
    srapl_program_advanced = '''
$PARTS:
1.0, 1.0, 2.0, 1.0, 0.5, 0.5, 1.5;

$PROGRAMM
# X[0] = kierunek do zasobu (z skanera)
# X[1] = odległość do zasobu (z skanera)

# Krok 1: Skanuj
f_2(1.0, 1.0);
'''

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

    # Włącz debug_interpreter=True dla szczegółowych logów interpretera
    automaton = Automaton(
        program_code=srapl_program,
        parts_genome=genome,
        world=world,
        position=(15, 15),
        debug_interpreter=False
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()

