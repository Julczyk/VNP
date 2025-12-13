RESOURCE_COLORS = {
    "coal": arcade.color.DARK_GRAY,
    "copper": arcade.color.COPPER,
    "iron": arcade.color.LIGHT_SLATE_GRAY,
    "gold": arcade.color.GOLD,
    "uranium": arcade.color.LIME_GREEN,
}

LAND_COLOR = arcade.color.DARK_SPRING_GREEN
import arcade
from map import World
from tile import WaterTile

TILE_SIZE = 20
SCREEN_MARGIN = 20

RESOURCE_COLORS = {
    "coal": arcade.color.DARK_GRAY,
    "copper": arcade.color.COPPER,
    "iron": arcade.color.LIGHT_SLATE_GRAY,
    "gold": arcade.color.GOLD,
    "uranium": arcade.color.LIME_GREEN,
}

LAND_COLOR = arcade.color.DARK_SPRING_GREEN


class WorldView(arcade.Window):
    def __init__(self, world: World):
        width = world.width * TILE_SIZE + SCREEN_MARGIN * 2
        height = world.height * TILE_SIZE + SCREEN_MARGIN * 2
        super().__init__(width, height, "World visualization")

        self.world = world
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()

        for i in range(self.world.height):
            for j in range(self.world.width):
                tile = self.world.map[i, j]

                x = SCREEN_MARGIN + j * TILE_SIZE + TILE_SIZE / 2
                y = SCREEN_MARGIN + i * TILE_SIZE + TILE_SIZE / 2

                # woda
                if isinstance(tile, WaterTile):
                    depth = min(tile.depth, 1.0)
                    blue = int(150 + 105 * depth)
                    color = (0, 0, blue)
                else:
                    # land
                    color = LAND_COLOR

                    if tile.materials:
                        resource = list(tile.materials.keys())[0]
                        color = RESOURCE_COLORS.get(resource, LAND_COLOR)

                arcade.draw_lbwh_rectangle_filled(
                    x,
                    y,
                    TILE_SIZE,
                    TILE_SIZE,
                    color
                )


if __name__ == "__main__":
    world = World(30, 30, seed=10)
    window = WorldView(world)
    arcade.run()

