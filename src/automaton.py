from parts import Part, Engine, Scanner, Storage
from config import FunctionID
from interpreter import Interpreter


class Automaton:
    def __init__(self, program_code, parts_genome, world, position):
        self.world = world
        self.position = position
        self.alive = True
        self.parts_genome = parts_genome

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
        """Suma mas części + masy ładunku ze wszystkich magazynów."""
        parts_mass = sum(p.mass for p in self.parts)
        
        cargo_mass = sum(
            storage.get_cargo_mass()
            for storage in self.get_storage_parts()
        )

        return parts_mass + cargo_mass
    
    def get_storage_parts(self):
        """Zwraca listę wszystkich części typu Storage w tym automacie"""
        from parts import Storage
        return [p for p in self.parts if isinstance(p, Storage)]


    def update(self):
        """
        Jeden krok symulacji dla tego automatu.
        1. Uruchom program -> wybierz funkcję.
        2. Uruchom funkcję części.
        3. Pobierz pasywną energię / koszta.
        """
        if not self.alive:
            return

        # 1. Wybór akcji przez program
        func_id, args = self.interpreter.run_step(self)

        # 2. Wykonanie akcji
        if func_id in self.part_map:
            part = self.part_map[func_id]
            part.execute_action(self, args)

        # 3. Koszty pasywne
        total_passive_drain = sum(p.passive_energy_drain for p in self.parts)
        self.energy -= total_passive_drain

        if self.can_reproduce():
            child = self.reproduce()
            if child is not None:
                # rejestracja w świecie – jeśli świat to obsługuje (?)
                for method_name in ("add_automaton", "spawn_automaton", "register_automaton"):
                    adder = getattr(self.world, method_name, None)
                    if callable(adder):
                        adder(child)
                        break

        if self.energy <= 0:
            self.die()

    def consume_energy(self, amount):
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False
    
    def can_reproduce(self):
        """
        Sprawdza, czy automat ma w magazynach komplet części
        potrzebnych do zbudowania kopii siebie
        """
        from config import PART_RESOURCE_MAP

        storages = self.get_storage_parts()
        if not storages:
            return False

        # Sumujemy zawartość wszystkich magazynów
        available = {}
        for storage in storages:
            for res, amt in storage.contents.items():
                available[res] = available.get(res, 0) + amt

        # Sprawdzamy, czy mamy wszystkie wymagane części
        for part_cls, _scale in self.parts_genome:
            part_name = part_cls.__name__

            if part_name not in PART_RESOURCE_MAP:
                continue

            needed_res = PART_RESOURCE_MAP[part_name]

            if available.get(needed_res, 0) < 1:
                return False

        return True
    
    def reproduce(self):
        """
        Tworzy nowy automat i usuwa zużyte części z magazynu.
        Zakładamy, że can_reproduce() == True.
        """
        from config import PART_RESOURCE_MAP

        storages = self.get_storage_parts()
        if not storages:
            return None

        # Zużycie części
        for part_cls, _scale in self.parts_genome:
            part_name = part_cls.__name__

            if part_name not in PART_RESOURCE_MAP:
                continue

            res_type = PART_RESOURCE_MAP[part_name]
            remaining = 1

            for storage in storages:
                have = storage.contents.get(res_type, 0)
                if have <= 0:
                    continue

                take = min(have, remaining)
                storage.contents[res_type] -= take
                remaining -= take

                if remaining == 0:
                    break

        # Stworzenie nowego automatu
        child = Automaton(
            program_code=self.interpreter.program,
            parts_genome=self.parts_genome,
            world=self.world,
            position=self.position
        )

        return child


    def die(self):
        """
        Oznacza automat jako martwy i próbuje usunąć go ze świata,
        jeśli świat udostępni odpowiednią metodę
        """
        if not self.alive:
            return

        self.alive = False

        # Nie wiem jak ta metoda będzie się nazywała w świecie,
        # więc testuję nazwy...
        for method_name in ("remove_automaton", "remove_robot", "kill_automaton", "unregister_automaton"):
            remover = getattr(self.world, method_name, None)
            if callable(remover):
                try:
                    remover(self)
                except TypeError:
                    pass
                break
