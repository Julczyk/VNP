import math
from abc import ABC, abstractmethod
from config import FunctionID, ResourceType


class Part(ABC):
    """
    Klasa bazowa dla wszystkich części automatu.
    """

    def __init__(self, scale: float):
        self.scale = scale
        # Masa i zużycie energii skalują się liniowo lub nieliniowo
        self.mass = 10.0 * scale
        self.passive_energy_drain = 0.1 * scale
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
        """
        f_1(dir, dist).
        Porusza robotem. Koszt zależy od masy całkowitej robota.
        """
        direction = int(args[0])
        distance = min(args[1], self.scale * 10)  # Max dystans zależy od skali

        # Obliczenie kosztu energii (Masa * Dystans * Współczynnik)
        energy_req = robot.get_total_mass() * distance * 0.05

        if robot.consume_energy(energy_req):
            robot.world.move_robot(robot, direction, distance)
        else:
            # Brak energii - ruch nieudany, powinno wyczerpać energię do zera i się zatrzymać
            pass


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

    def add_item(self, item_type, amount):
        # Dodaje przedmiot, jeśli jest miejsce. Jeśli nie - ucina lub anuluje
        pass

    def get_cargo_mass(self):
        """ Zwraca całkowitą masę ładunku w tym magazynie."""
        from config import RESOURCE_MASS

        total_mass = 0.0
        for resource, amount in self.contents.items():
            mass_per_unit = RESOURCE_MASS.get(resource, 0.0)
            total_mass += mass_per_unit * amount

        return total_mass

class PowerGenerator(Part):
    """ Źródło energii (abstrakcyjnie) """

    def __init__(self, scale):
        super().__init__(scale)
        self.energy_output = 2.0 * scale   # ile energii produkuje w IDLE

    def get_function_id(self):
        return FunctionID.IDLE.value

    def execute_action(self, robot, args: list[float]):
        """ IDLE -> produkcja energii """
        robot.energy += self.energy_output
        return True

    # można dodać więcej typów generatorów energii tutaj (jakieś paliwo, słońce itp.)

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
