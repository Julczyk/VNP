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

# ... (Implementacja Huty, Assemblera analogicznie)