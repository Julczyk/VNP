import numpy as np
from tile import Tile, WaterTile, RESOURCES
from perlin_noise import PerlinNoise

class World:
    def __init__(self, height: int, width: int, seed: int):
        self.map = np.empty(shape=[height, width], dtype=object)
        self.water_map = np.zeros((height, width), dtype=bool)
        self.depth_map = np.zeros((height, width), dtype=float)
        self.height = height
        self.width = width
        self.seed = seed
        self.generate_map()
    
    def generate_map(self):
        self.generate_river_noise()
        noise = {r: PerlinNoise(octaves=4, seed=self.seed + i)
                          for i, r in enumerate(RESOURCES)}
        for i in range(self.height):
            for j in range(self.width):
                if self.water_map[i][j]:
                    self.map[i, j] = WaterTile(self.depth_map[i,j])
                else:
                    current_resource_status = {r: noise[r]([i/100, j/100]) for r in noise.keys()}
                    self.map[i, j] = Tile(current_resource_status)

    def generate_river_noise(self):
        noise = PerlinNoise(octaves=5, seed=self.seed + 100)
        threshold = -0.15
        for i in range(self.height):
            for j in range(self.width):
                val = noise([i / 30, j / 30])
                if val < threshold:
                    self.water_map[i, j] = True
                    depth = (threshold - val) / threshold
                    self.depth_map[i, j] = depth

    # Roboczo - 1 jak jest surowiec 0 jak go nie ma     TO BE DELETED LATER
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
    print(world.map)