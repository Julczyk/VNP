from parts import Part, Engine, Scanner, Storage, FunctionID
from interpreter import Interpreter


class Automaton:
    def __init__(self, program_code, parts_genome, world, position):
        self.world = world
        self.position = position

        # Pamięć i Program
        self.memory = [0.0] * 64
        self.interpreter = Interpreter(program_code)

        # Budowanie robota z genomu (listy par (PartType, Scale))
        self.parts = []
        self.part_map = {}  # Mapowanie ID funkcji na instancję części
        self._assemble_robot(parts_genome)

        self.energy = 100.0  # Startowa energia

    def _assemble_robot(self, genome):
        """Tworzy instancje części na podstawie genomu."""
        for part_cls, scale in genome:
            part_instance = part_cls(scale)
            self.parts.append(part_instance)
            # Rejestracja obsługi f_n
            self.part_map[part_instance.get_function_id()] = part_instance

    def get_total_mass(self):
        """Suma mas części + ładunku"""
        parts_mass = sum(p.mass for p in self.parts)
        cargo_mass = 0  # TODO: pobrać z części Storage
        return parts_mass + cargo_mass

    def update(self):
        """
        Jeden krok symulacji dla tego automatu.
        1. Uruchom program -> wybierz funkcję.
        2. Uruchom funkcję części.
        3. Pobierz pasywną energię / koszta.
        """
        # 1. Wybór akcji przez program
        func_id, args = self.interpreter.run_step(self)

        # 2. Wykonanie akcji
        if func_id in self.part_map:
            part = self.part_map[func_id]
            part.execute_action(self, args)
        elif func_id == FunctionID.IDLE.value:
            # Logika dla braku akcji (np. ładowanie PV jeśli jest)
            pass

        # 3. Koszty pasywne
        total_passive_drain = sum(p.passive_energy_drain for p in self.parts)
        self.energy -= total_passive_drain

        if self.energy <= 0:
            self.die()

    def consume_energy(self, amount):
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def die(self):
        # Usunięcie z symulacji
        pass