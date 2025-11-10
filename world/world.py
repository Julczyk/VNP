import numpy as np
from tile import Tile
from perlin_noise import PerlinNoise

class World:
    def __init__(self, height: int, width: int, seed: int):
        self.map = np.empty(shape=[height, width], dtype=object);
        self.height = height
        self.width = width
        self.seed = seed
        self.generate_map()
    
    def generate_map(self):
        noise = PerlinNoise(octaves=4, seed=self.seed)
        for i in range(self.height):
            for j in range(self.width):
                self.map[i, j] = Tile(noise([i/100, j/100]))

    # Roboczo - 1 jak jest surowiec 0 jak go nie ma
    def get_simplified_map(self):
        simplified_map = np.zeros(self.map.shape)
        for i, row in enumerate(self.map):
            for j, tile in enumerate(row):
                if len(tile.materials):
                    simplified_map[i][j] = 1
        return simplified_map
    
world = World(10,10, 10)
print(world.get_simplified_map())