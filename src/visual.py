from map import World # Import klasy World – generuje proceduralną mapę z Perlin noise
import arcade

TILE_SIZE = 16 # Rozmiar jednego kafelka w pikselach

class WorldWindow(arcade.Window):
    # rysowanie kafelków w czasie rzeczywistym

    def __init__(self, world):
        # ustawienie rozmiaru okna na rozmiar świata (szerokosc * rozmiar kafla, wysokosc * rozmiar kafla)
        super().__init__(world.width * TILE_SIZE, world.height * TILE_SIZE, "World")
        self.world = world

    def on_draw(self):
        # w tej funkcji rysuje mape
        self.clear()
        for i in range(self.world.height):
            for j in range(self.world.width):
                tile = self.world.map[i][j] # pobranie kafla tile

                if "steel" in tile.materials: #jezeli kafel ma stal -> kolorujemy na zolto
                    color = arcade.color.GOLD
                else:
                    color = arcade.color.DARK_GRAY # jesli nie -> kolorujemy na szaro

                # wspolrzedne prostokata ktory rysujemy
                arcade.draw_lrbt_rectangle_filled(
                    left=j * TILE_SIZE,
                    right=j * TILE_SIZE + TILE_SIZE,
                    bottom=i * TILE_SIZE,
                    top=i * TILE_SIZE + TILE_SIZE,
                    color=color
                )

world = World(50, 50, 10)
window = WorldWindow(world)
arcade.run()
