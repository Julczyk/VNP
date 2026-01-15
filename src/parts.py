import math
from abc import ABC, abstractmethod
from config import FunctionID, ResourceType
import random

class Part(ABC):
    """
    Klasa bazowa dla wszystkich części automatu.
    """

    def __init__(self, scale: float):
        self.scale = scale
        # Masa i zużycie energii skalują się liniowo lub nieliniowo
        self.mass = 10.0 * scale
        self.passive_energy_drain = 0.01 * scale
        self.active_energy_cost = 1.0 * scale

    @abstractmethod
    def get_function_id(self) -> int:
        pass

    @abstractmethod
    def execute_action(self, robot, args: list[float]):
        """
        Wykonuje logikę danej części. Zwraca True, jeśli akcja się powiodła.
        Modyfikuje stan robota lub świata.
        """
        pass

class Engine(Part):
    def get_function_id(self):
        return FunctionID.MOVE.value

    def execute_action(self, robot, args: list[float]):
        # --- direction ---
        if isinstance(args[0], str) and args[0].startswith("MEM"):
            mem_idx = int(args[0][3:])
            direction = int(robot.memory[mem_idx])
        else:
            direction = int(args[0])

        # --- distance ---
        if isinstance(args[1], str) and args[1].startswith("MEM"):
            mem_idx = int(args[1][3:])
            distance = int(robot.memory[mem_idx])
        else:
            distance = int(args[1])

        # jeśli nie mamy celu / bez sensu → losowy krok
        if direction < 0 or distance <= 0:
            direction = random.randint(0, 3)
            distance = 1

        distance = min(distance, int(self.scale * 10))

        energy_req = robot.get_total_mass() * distance * 0.05

        if robot.consume_energy(energy_req):
            robot.world.move_robot(robot, direction, 1)
            return True

        return False


class Scanner(Part):
    def get_function_id(self):
        return FunctionID.SCAN.value

    def execute_action(self, robot, args: list[float]):
        """
        f_2(pow, res_type).
        Skanuje otoczenie i zapisuje wynik do pamięci.
        """
        radius = self.scale * 5
        target_res = int(args[1]) if len(args) > 1 else None

        if robot.consume_energy(self.active_energy_cost):
            result = robot.world.scan_area(robot.position, radius, target_res)
            # Zapisz wynik do pamięci (np. kierunek i odległość)
            # Konwencja: X[0] = dir, X[1] = dist
            robot.memory[0] = result['dir']
            robot.memory[1] = result['dist']
            if result['dir'] < 0:
                robot.memory[1] = -1  # wymuś losowy krok w Engine

class Storage(Part):
    def __init__(self, scale):
        super().__init__(scale)
        self.capacity = scale * 100  #
        self.contents = {}  # Słownik {ResourceType: amount}

    def get_function_id(self):
        return FunctionID.STORE.value

    def execute_action(self, robot, args: list[float]):
        # Implementacja zrzucania ładunku f_3(amount, type)
        pass

    def has_space(self, amount: float) -> bool:
        """Sprawdza czy jest miejsce na nowy ładunek."""
        current_load = sum(self.contents.values())
        return (current_load + amount) <= self.capacity

    def get_cargo_mass(self):
        """ Zwraca całkowitą masę ładunku w tym magazynie."""
        from config import RESOURCE_MASS

        total_mass = 0.0
        for resource, amount in self.contents.items():
            mass_per_unit = RESOURCE_MASS.get(resource, 0.0)
            total_mass += mass_per_unit * amount

        return total_mass
    
    def add_item(self, item_type, amount):
        if not self.has_space(amount):
            return False

        self.contents[item_type] = self.contents.get(item_type, 0) + amount
        return True


class PowerGenerator(Part):
    """ Źródło energii (pasywne) """

    def __init__(self, scale):
        super().__init__(scale)
        self.energy_output = 5.0 * scale

    def get_function_id(self):
        # Generator NIE jest wywoływany jako akcja
        return None

    def execute_action(self, robot, args):
        # Generator nie wykonuje aktywnej akcji
        return False

    def produce_energy(self, robot):
        robot.energy = min(robot.energy + self.energy_output, robot.max_energy)

# ... (Implementacja Huty, Assemblera analogicznie)
class Smelter(Part):
    def get_function_id(self):
        return FunctionID.SMELT.value

    def execute_action(self, robot, args: list[float]):
        """
        f_4(amount)
        Przetwarza RAW_ORE -> PROCESSED_METAL
        """
        amount = max(1, int(args[0]))  # ilość jednostek rudy
        energy_cost = amount * self.active_energy_cost

        storage = self._get_storage(robot)
        if storage is None:
            return False

        # Sprawdzenia niepodzielności
        if storage.contents.get(ResourceType.RAW_ORE, 0) < amount:
            return False

        if not storage.has_space(amount):
            return False

        if not robot.consume_energy(energy_cost):
            return False

        # Wykonanie procesu
        storage.contents[ResourceType.RAW_ORE] -= amount
        storage.add_item(ResourceType.PROCESSED_METAL, amount)
        return True

    def _get_storage(self, robot):
        for p in robot.parts:
            if isinstance(p, Storage):
                return p
        return None


PART_RECIPES = {
    ResourceType.PART_ENGINE: {
        ResourceType.PROCESSED_METAL: 10,
        "energy": 20
    },
    ResourceType.PART_SCANNER: {
        ResourceType.PROCESSED_METAL: 8,
        "energy": 15
    }
}


class Assembler(Part):
    def get_function_id(self):
        return FunctionID.ASSEMBLE.value

    def execute_action(self, robot, args: list[float]):
        """
        f_5(partID)
        Produkuje część i odkłada ją do magazynu
        """
        part_id = int(args[0])
        part_type = ResourceType(part_id)

        if part_type not in PART_RECIPES:
            return False

        recipe = PART_RECIPES[part_type]
        storage = self._get_storage(robot)
        if storage is None:
            return False

        # Sprawdzenie zasobów
        for res, amt in recipe.items():
            if res == "energy":
                continue
            if storage.contents.get(res, 0) < amt:
                return False

        if not storage.has_space(1):
            return False

        if not robot.consume_energy(recipe["energy"] * self.scale):
            return False

        # Zużycie zasobów
        for res, amt in recipe.items():
            if res == "energy":
                continue
            storage.contents[res] -= amt

        # Dodanie gotowej części
        storage.add_item(part_type, 1)
        return True

    def _get_storage(self, robot):
        for p in robot.parts:
            if isinstance(p, Storage):
                return p
        return None

class Collector(Part):
    """
    Część odpowiedzialna za zbieranie zasobów z kafelka,
    na którym znajduje się automat.
    """

    def get_function_id(self):
        return FunctionID.COLLECT.value

    def execute_action(self, robot, args: list[float]):
        """
        f_COLLECT(amount)
        Zbiera zasoby z aktualnego kafelka lub sąsiedztwa.
        """
        print(">>> COLLECT EXECUTED")

        # --- 1. Ile zbieramy ---
        amount = int(args[0]) if args else 1
        amount = max(1, amount)

        # --- 2. Koszt energetyczny ---
        energy_cost = amount * self.active_energy_cost
        if not robot.consume_energy(energy_cost):
            return False

        # --- 3. Pozycje do sprawdzenia (zasięg manipulacyjny) ---
        x, y = robot.position
        positions = [
            (x, y),
            (x + 1, y), (x - 1, y),
            (x, y + 1), (x, y - 1),
        ]

        # --- 4. Magazyn ---
        storages = robot.get_storage_parts()
        if not storages:
            return False
        storage = storages[0]

        # --- 5. Próba zebrania ---
        for pos in positions:
            if not (0 <= pos[0] < robot.world.width and 0 <= pos[1] < robot.world.height):
                continue

            collected = robot.world.take_resources(pos, amount)
            if collected:
                for res, amt in collected.items():
                    storage.contents[res] = storage.contents.get(res, 0) + amt

                robot.energy = min(robot.max_energy, robot.energy + 3)

                robot.last_collected_tick = robot.world.tick
                robot.memory[1] = -1  # wymuś nowe skanowanie

                print(f"[Tick {robot.world.tick}] COLLECTED {collected} at {pos}")
                return True

        return False

