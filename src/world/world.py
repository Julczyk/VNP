from importlib import resources
from turtle import position
import numpy as np
from world.tile import Tile, WaterTile
from perlin_noise import PerlinNoise
from config import ResourceType, RESOURCE_THRESHOLD, RESOURCE_GENERATION
import random
import radius
from world.tile import WaterTile

RESOURCE_DENSITY = 0.12 

class World:
    def __init__(self, height: int, width: int, seed: int):
        self.map = np.empty(shape=[height, width], dtype=object)
        self.water_map = np.zeros((height, width), dtype=bool)
        self.depth_map = np.zeros((height, width), dtype=float)
        self.height = height
        self.width = width
        self.seed = seed
        self.automata = []
        self.wrecks = []
        self.tick = 0
        self.generate_map()
        print("=== WORLD INIT ===")
        for y in range(self.height):
            for x in range(self.width):
                tile = self.get_tile((x, y))
                if tile.materials:
                    print(f"RESOURCE AT {(x,y)} -> {tile.materials}")

    
    def generate_map(self):
        # 1. wygeneruj mapy pomocnicze
        self.generate_river_noise()
        self.generate_resource_noise()

        # 2. STWÓRZ KAFELKI
        for y in range(self.height):
            for x in range(self.width):
                if self.water_map[y, x]:
                    self.map[y, x] = WaterTile(depth=self.depth_map[y, x])
                else:
                    self.map[y, x] = Tile()

        # 3. GENERACJA ZASOBÓW
        resource_types = list(RESOURCE_GENERATION.keys())
        weights = [RESOURCE_GENERATION[r]["weight"] for r in resource_types]

        for y in range(self.height):
            for x in range(self.width):
                tile = self.map[y, x]
                if isinstance(tile, WaterTile):
                    continue

                best_res = None
                best_n = None

                for res, noise in self.resource_noise.items():
                    n = (noise([x / 80, y / 80]) + 1) / 2

                    threshold = RESOURCE_THRESHOLD.get(res, 0.3)
                    if n < threshold:
                        continue

                    if best_n is None or n > best_n:
                        best_n = n
                        best_res = res

                if best_res is None:
                    continue

                min_amt, max_amt = RESOURCE_GENERATION[best_res]["amount"]
                strength = (best_n + 1) / 2
                amt = int(min_amt + strength * (max_amt - min_amt))

                if amt > 0:
                    tile.materials[best_res] = amt

        self.generate_raw_ore_clusters()

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

    def generate_resource_noise(self):
        self.resource_noise = {
            res: PerlinNoise(octaves=4, seed=self.seed + i * 37)
            for i, res in enumerate(RESOURCE_GENERATION.keys())
        }

    def generate_raw_ore_clusters(self):
        num_clusters = max(1, int(self.width * self.height * 0.01))
        cluster_radius = max(2, min(self.width, self.height) // 20)

        for _ in range(num_clusters):
            cx = random.randint(0, self.width - 1)
            cy = random.randint(0, self.height - 1)
            if isinstance(self.map[cy, cx], WaterTile):
                continue

            for dy in range(-cluster_radius, cluster_radius + 1):
                for dx in range(-cluster_radius, cluster_radius + 1):
                    x = cx + dx
                    y = cy + dy

                    if x < 0 or y < 0 or x >= self.width or y >= self.height:
                        continue
                    if isinstance(self.map[y, x], WaterTile):
                        continue

                    tile = self.map[y, x]

                    dist = (dx ** 2 + dy ** 2) ** 0.5
                    if dist > cluster_radius:
                        continue

                    prob = max(0.3, 1 - dist / cluster_radius)

                    if random.random() < prob:
                        min_amt, max_amt = RESOURCE_GENERATION[ResourceType.RAW_ORE]["amount"]
                        amt = random.randint(min_amt, max_amt)
                        tile.materials[ResourceType.RAW_ORE] = amt

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
    
    def take_resources(self, position, amount):
        tile = self.get_tile(position)
        if not tile.materials:
            return {}

        collected = {}

        for res, available in list(tile.materials.items()):
            take = min(amount, available)

            if take > 0:
                collected[res] = take
                tile.materials[res] -= take

                if tile.materials[res] <= 0:
                    del tile.materials[res]

                break  # zbieramy jeden typ naraz

        return collected

    
    def add_automaton(self, automaton):
        self.automata.append(automaton)

    def remove_automaton(self, automaton):
        if automaton in self.automata:
            self.automata.remove(automaton)

    def drop_resources(self, position, resources):
        x, y = position
        tile = self.map[y, x]

        for res, amt in resources.items():
            tile.materials[res] = tile.materials.get(res, 0) + amt
    
    def move_robot(self, robot, direction, distance):
        dx, dy = {
            0: (0, 1),
            1: (1, 0),
            2: (0, -1),
            3: (-1, 0),
        }.get(direction, (0, 0))

        x, y = robot.position

        for _ in range(int(distance)):
            nx = max(0, min(self.width - 1, x + dx))
            ny = max(0, min(self.height - 1, y + dy))

            if isinstance(self.map[ny, nx], WaterTile):
                break

            x, y = nx, ny

        robot.position = (x, y)

    def scan_area(self, position, radius, target_res=None):
        x0, y0 = position
        best_dist = None
        best_dir = 0

        for dy in range(-int(radius), int(radius)+1):
            for dx in range(-int(radius), int(radius)+1):
                x = x0 + dx
                y = y0 + dy

                if x < 0 or y < 0 or x >= self.width or y >= self.height:
                    continue

                tile = self.map[y, x]
                if not tile.materials:
                    continue

                dist = abs(dx) + abs(dy)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    # bardzo prosta konwencja kierunku
                    if abs(dx) > abs(dy):
                        best_dir = 1 if dx > 0 else 3
                    else:
                        best_dir = 0 if dy > 0 else 2

        if best_dist is None:
            return {"dir": -1, "dist": 0}

        return {"dir": best_dir, "dist": best_dist}

    def get_tile(self, position):
        x, y = position
        return self.map[y][x]
    
    def update(self):
        """
        Jeden krok symulacji świata.
        Aktualizuje wszystkie automaty.
        """
        for automaton in list(self.automata):
            automaton.update()
        self.tick += 1
        print("WORLD UPDATE", len(self.automata))

    def add_wreck(self, position, resources):
        x, y = position
        self.wrecks.append((x, y, resources))
        self.drop_resources(position, resources)

    def count_automata_near(self, position, radius=1):
        x0, y0 = position
        count = 0

        for automaton in self.automata:
            x, y = automaton.position
            if abs(x - x0) <= radius and abs(y - y0) <= radius:
                count += 1

        return count


if __name__ == "__main__":
    world = World(30,30, 10)
    print(world.map)
