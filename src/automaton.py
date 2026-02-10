from parts import Part, Engine, Scanner, Storage
from config import FunctionID, ResourceType, STATS_REPORT_INTERVAL, get_function_to_part_map
from srapl_interpreter import SRAPLInterpreter as Interpreter
from stats import stats_manager, AutomatonStats

REPRODUCTION_ENERGY_COST = 10

class Automaton:
    def __init__(self, program_code, parts_genome, world, position, debug_interpreter=False):
        self.world = world
        self.position = position
        self.alive = True
        self.parts_genome = parts_genome
        self.max_energy = 300.0
        self.birth_tick = world.tick
        self.children_count = 0

        # Pamięć i Program
        self.memory = [0.0] * 64
        self.interpreter = Interpreter(program_code, debug=True)

        # Budowanie robota z genomu (listy par (PartType, Scale))
        self.parts = []
        self.part_map = {}  # Mapowanie ID funkcji na instancję części
        self._assemble_robot(parts_genome)

        self.energy = 100.0  # Startowa energia

        # System statystyk
        self.stats: AutomatonStats = stats_manager.create_stats(self.birth_tick)

    def _assemble_robot(self, genome):
        """Tworzy instancje części na podstawie genomu."""
        # Pobierz mapowanie funkcji na klasy części
        func_to_part_cls = get_function_to_part_map()

        for part_cls, scale in genome:
            part_instance = part_cls(scale)
            self.parts.append(part_instance)

            # Znajdź FunctionID dla tej klasy części
            for func_id, mapped_cls in func_to_part_cls.items():
                if mapped_cls == part_cls:
                    self.part_map[func_id] = part_instance
                    break

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
        print(
            f"[Tick {self.world.tick}] Energy={self.energy:.1f} "
            f"Storage={[(s.contents) for s in self.get_storage_parts()]}"
        )

        if not self.alive:
            return

        # Rejestruj krok w statystykach
        self.stats.record_step()

        # Zapamiętaj pozycję przed ruchem (do obliczenia dystansu)
        old_position = self.position

        # 1. Wybór akcji przez program
        func_id, args = self.interpreter.run_step(self)

        # Normalizuj func_id do FunctionID enum
        if isinstance(func_id, int):
            try:
                func_id = FunctionID(func_id)
            except ValueError:
                pass  # Nieznane ID - zostaw jako int

        # 2. Wykonanie akcji
        actual_fid = func_id.value if hasattr(func_id, 'value') else func_id

        if actual_fid != FunctionID.IDLE.value and actual_fid in self.part_map:
            part = self.part_map[actual_fid]
        if func_id in self.part_map:
            part = self.part_map[func_id]
            part.execute_action(self, args)

        # Oblicz i zarejestruj przebytą odległość
        if self.position != old_position:
            dx = self.position[0] - old_position[0]
            dy = self.position[1] - old_position[1]
            distance = (dx**2 + dy**2) ** 0.5
            self.stats.record_movement(distance)

        # 3. Koszty pasywne
        total_passive_drain = sum(p.passive_energy_drain for p in self.parts)
        passive_cost = total_passive_drain + 1.0
        self.energy -= passive_cost
        self.stats.record_energy_consumed(passive_cost)

        # 4. IDLE = produkcja energii
        if func_id == FunctionID.IDLE:
            for part in self.parts:
                if hasattr(part, "produce_energy"):
                    energy_before = self.energy
                    part.produce_energy(self)
                    energy_gained = self.energy - energy_before
                    if energy_gained > 0:
                        self.stats.record_energy_produced(energy_gained)

        self.share_resources_with_neighbors()

        if self.can_reproduce():
            child = self.reproduce()
            if child is not None:
                # Rejestruj potomka w statystykach
                self.stats.record_offspring()
                # rejestracja w świecie – jeśli świat to obsługuje (?)
                for method_name in ("add_automaton", "spawn_automaton", "register_automaton"):
                    adder = getattr(self.world, method_name, None)
                    if callable(adder):
                        adder(child)
                        break

        print(
            f"[Tick {self.world.tick}] can_reproduce={self.can_reproduce()}"
        )

        # Okresowe raportowanie statystyk
        if stats_manager.should_report(self.stats, self.world.tick):
            stats_manager.report(self.stats, self.world.tick, "periodic")

        self.memory[0] = self.energy / self.max_energy

        if self.energy <= 0:
            self.die()

    def consume_energy(self, amount):
        if self.energy >= amount:
            self.energy -= amount
            self.stats.record_energy_consumed(amount)
            return True
        return False
    
    def share_resources_with_neighbors(self):
        neighbors = [
            a for a in self.world.automata
            if a != self and abs(a.position[0] - self.position[0]) <= 1 and abs(a.position[1] - self.position[1]) <= 1
        ]
        if not neighbors:
            print(f"[Tick {self.world.tick}] Automaton at {self.position} has no neighbors to share resources with.")
            return

        storages = self.get_storage_parts()
        if not storages:
            print(f"[Tick {self.world.tick}] Automaton at {self.position} has no storage parts.")
            return

        print(f"[Tick {self.world.tick}] Automaton at {self.position} is attempting to share resources with {len(neighbors)} neighbors.")

        for res_type in ResourceType:
            total_amount = sum(storage.contents.get(res_type, 0) for storage in storages)
            avg_amount = total_amount / (len(neighbors) + 1)

            for neighbor in neighbors:
                neighbor_storages = neighbor.get_storage_parts()
                neighbor_amount = sum(storage.contents.get(res_type, 0) for storage in neighbor_storages)

                if neighbor_amount < avg_amount and total_amount > avg_amount:
                    transfer = min(total_amount - avg_amount, avg_amount - neighbor_amount, 1)  # max 1 jednostka na transfer

                    print(f"Sharing {transfer} of {res_type.name} from {self.position} to {neighbor.position}")

                    # Usuń z własnych magazynów
                    remaining = transfer
                    for storage in storages:
                        have = storage.contents.get(res_type, 0)
                        if have <= 0:
                            continue
                        take = min(have, remaining)
                        storage.contents[res_type] -= take
                        remaining -= take
                        if remaining <= 0:
                            break

                    # Dodaj do magazynów sąsiada
                    if neighbor_storages:
                        neighbor_storages[0].contents[res_type] = neighbor_storages[0].contents.get(res_type, 0) + transfer

    
    def can_reproduce(self):
        """
        Sprawdza, czy automat ma wystarczającą ilość surowców,
        aby stworzyć kopię siebie.
        (Uproszczona wersja – bez pełnej produkcji części)
        """
        from config import ResourceType

        storages = self.get_storage_parts()
        if not storages:
            return False

        total_ore = 0
        for storage in storages:
            total_ore += storage.contents.get(ResourceType.RAW_ORE, 0)

        # koszt reprodukcji (łatwo regulować trudność)
        REQUIRED_ORE = 5

        return total_ore >= REQUIRED_ORE

    
    def reproduce(self):
        """
        Tworzy nowy automat i usuwa zużyte części z magazynu.
        Zakładamy, że can_reproduce() == True.
        """
        from config import PART_RESOURCE_MAP
        from world.tile import WaterTile
        import random

        if self.world.tick - self.birth_tick < 20:
            return None

        if self.energy < REPRODUCTION_ENERGY_COST:
            return None
        
        MAX_LOCAL_DENSITY = 6

        if self.world.count_automata_near(self.position, radius=1) > MAX_LOCAL_DENSITY:
            return None

        storages = self.get_storage_parts()
        if not storages:
            return None

        # --- Zużycie części ---
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

        # --- WYBÓR POZYCJI DLA DZIECKA ---
        x, y = self.position
        candidates = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]

        # w granicach mapy
        candidates = [
            (cx, cy)
            for cx, cy in candidates
            if 0 <= cx < self.world.width and 0 <= cy < self.world.height
        ]

        random.shuffle(candidates)

        spawn_pos = self.position  # fallback
        for pos in candidates:
            tile = self.world.get_tile(pos)
            if not isinstance(tile, WaterTile):
                spawn_pos = pos
                break

        self.consume_energy(REPRODUCTION_ENERGY_COST)

        # --- STWORZENIE DZIECKA ---
        child = Automaton(
            program_code=self.interpreter.program,
            parts_genome=self.parts_genome,
            world=self.world,
            position=spawn_pos
        )

        self.children_count += 1

        return child


    def die(self):
        if not self.alive:
            return

        self.alive = False

        # Raportuj statystyki przy śmierci
        stats_manager.report(self.stats, self.world.tick, "death")

        # zasoby z wraku
        wreck_resources = {}

        # zawartość magazynów
        for storage in self.get_storage_parts():
            for res, amt in storage.contents.items():
                wreck_resources[res] = wreck_resources.get(res, 0) + amt

        # części → metal
        from config import ResourceType
        metal = int(sum(p.mass for p in self.parts) * 0.3)
        if metal > 0:
            wreck_resources[ResourceType.PROCESSED_METAL] = (
                wreck_resources.get(ResourceType.PROCESSED_METAL, 0) + metal
            )

        # dodanie wraku do świata
        self.world.add_wreck(self.position, wreck_resources)

        # usunięcie z listy automatów
        if self in self.world.automata:
            self.world.automata.remove(self)


    def get_wreck_resources(self):
        """
        Zwraca dict {ResourceType: amount} zasobów,
        które pozostają po śmierci automatu.
        """

        wreck = {}

        # Zawartość magazynów
        for storage in self.get_storage_parts():
            for res, amt in storage.contents.items():
                wreck[res] = wreck.get(res, 0) + amt

        # Części automatu -> metal
        total_metal = 0
        for part in self.parts:
            total_metal += int(part.mass * 0.5)

        if total_metal > 0:
            wreck[ResourceType.PROCESSED_METAL] = (
                wreck.get(ResourceType.PROCESSED_METAL, 0) + total_metal
            )

        return wreck
