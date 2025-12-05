import numpy as np
from tile import Tile, RESOURCES
from perlin_noise import PerlinNoise

class World:
    def __init__(self, height: int, width: int, seed: int):
        self.map = np.empty(shape=[height, width], dtype=object);
        self.height = height
        self.width = width
        self.seed = seed
        self.generate_map()
    
    def generate_map(self):
        noise = {r: PerlinNoise(octaves=4, seed=self.seed + i)
                          for i, r in enumerate(RESOURCES)}
        for i in range(self.height):
            for j in range(self.width):
                current_resource_status = {r: noise[r]([i/100, j/100]) for r in noise.keys()}
                self.map[i, j] = Tile(current_resource_status)

    # Roboczo - 1 jak jest surowiec 0 jak go nie ma
    def get_simplified_map(self):
        simplified_map = np.zeros(self.map.shape)
        for i, row in enumerate(self.map):
            for j, tile in enumerate(row):
                if len(tile.materials):
                    simplified_map[i][j] = 1
        return simplified_map

    def get_resource_map(self):
        resource_map = np.zeros(self.map.shape, dtype=object)
        for i, row in enumerate(self.map):
            for j, tile in enumerate(row):
                if len(tile.materials):
                    resource_map[i][j] = list(tile.materials.keys())[0]
        return resource_map

if __name__ == "__main__":
    world = World(30,30, 10)
    print(world.get_resource_map())