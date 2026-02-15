"""
System statystyk automatów.

Zbiera informacje o działaniu automatu:
- liczba wykonanych kroków
- liczba zebranych zasobów
- przebyta odległość
- wyprodukowane części
- ilość potomków
- wyprodukowana i zużyta energia

Statystyki są niedostępne dla SRAPL - służą do oceny efektywności.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from config import ResourceType, STATS_REPORT_INTERVAL

logger = logging.getLogger('STATS')


@dataclass
class AutomatonStats:
    """Statystyki pojedynczego automatu."""

    # Identyfikacja
    automaton_id: int = 0
    parent_id: int = 0  # ID rodzica (0 jeśli brak)
    birth_tick: int = 0

    # Liczniki podstawowe
    steps_executed: int = 0
    distance_traveled: float = 0.0
    offspring_count: int = 0

    # Energia
    energy_produced: float = 0.0
    energy_consumed: float = 0.0

    # Zasoby zebrane (per typ)
    resources_collected: Dict[ResourceType, int] = field(default_factory=dict)

    # Części wyprodukowane (per typ)
    parts_produced: Dict[ResourceType, int] = field(default_factory=dict)
    
    # Specjalne: Przetworzone złoto
    gold_processed: int = 0

    # Ostatni tick raportowania
    last_report_tick: int = 0

    def record_step(self):
        """Rejestruje wykonanie kroku."""
        self.steps_executed += 1

    def record_movement(self, distance: float):
        """Rejestruje ruch o daną odległość."""
        self.distance_traveled += distance

    def record_resource_collected(self, resource_type: ResourceType, amount: int):
        """Rejestruje zebranie zasobu."""
        current = self.resources_collected.get(resource_type, 0)
        self.resources_collected[resource_type] = current + amount

    def record_part_produced(self, part_type: ResourceType, amount: int = 1):
        """Rejestruje wyprodukowanie części."""
        current = self.parts_produced.get(part_type, 0)
        self.parts_produced[part_type] = current + amount
        
    def record_gold_processed(self, amount: int):
        """Rejestruje przetworzenie złota."""
        self.gold_processed += amount

    def record_offspring(self):
        """Rejestruje narodziny potomka."""
        self.offspring_count += 1

    def record_energy_produced(self, amount: float):
        """Rejestruje wyprodukowaną energię."""
        self.energy_produced += amount

    def record_energy_consumed(self, amount: float):
        """Rejestruje zużytą energię."""
        self.energy_consumed += amount

    def get_total_resources_collected(self) -> int:
        """Zwraca łączną liczbę zebranych zasobów."""
        return sum(self.resources_collected.values())

    def get_total_parts_produced(self) -> int:
        """Zwraca łączną liczbę wyprodukowanych części."""
        return sum(self.parts_produced.values())

    def get_lifetime(self, current_tick: int) -> int:
        """Zwraca czas życia automatu w tickach."""
        return current_tick - self.birth_tick

    def calculate_fitness(self) -> float:
        """
        Oblicza fitness osobnika: ilość przetworzonego złota.
        """
        return float(self.gold_processed)

    def to_dict(self, current_tick: int) -> dict:
        """Konwertuje statystyki do słownika."""
        return {
            'automaton_id': self.automaton_id,
            'parent_id': self.parent_id,
            'birth_tick': self.birth_tick,
            'lifetime': self.get_lifetime(current_tick),
            'steps_executed': self.steps_executed,
            'distance_traveled': round(self.distance_traveled, 2),
            'offspring_count': self.offspring_count,
            'energy_produced': round(self.energy_produced, 2),
            'energy_consumed': round(self.energy_consumed, 2),
            'energy_balance': round(self.energy_produced - self.energy_consumed, 2),
            'total_resources_collected': self.get_total_resources_collected(),
            'resources_collected': {k.name: v for k, v in self.resources_collected.items()},
            'total_parts_produced': self.get_total_parts_produced(),
            'parts_produced': {k.name: v for k, v in self.parts_produced.items()},
            'gold_processed': self.gold_processed,
            'fitness_score': self.calculate_fitness(),
        }

    def format_report(self, current_tick: int, reason: str = "periodic") -> str:
        """Formatuje raport statystyk."""
        data = self.to_dict(current_tick)
        
        # Pobierz lineage fitness z managera
        lineage_fitness = stats_manager.calculate_lineage_fitness(self.automaton_id)

        lines = [
            f"=== STATS REPORT ({reason}) ===",
            f"Automaton ID: {data['automaton_id']} (Parent: {data['parent_id']})",
            f"Lifetime: {data['lifetime']} ticks",
            f"GOLD PROCESSED (Fitness): {data['gold_processed']}",
            f"LINEAGE FITNESS (Total Gold): {lineage_fitness}",
            f"Offspring: {data['offspring_count']}",
            f"Resources collected: {data['total_resources_collected']} total",
        ]
        
        if self.gold_processed > 0:
             lines.append(f"  *** GOLD SMELTER ***")

        lines.append("=" * 30)

        return "\n".join(lines)


class StatsManager:
    """
    Zarządza statystykami wszystkich automatów.
    Zbiera raporty i może je agregować.
    """

    def __init__(self):
        self._next_id = 1
        self._all_reports: list[dict] = []
        # Mapa id -> AutomatonStats (do obliczania lineage)
        self._stats_map: Dict[int, AutomatonStats] = {}

    def create_stats(self, birth_tick: int, parent_id: int = 0) -> AutomatonStats:
        """Tworzy nowy obiekt statystyk dla automatu."""
        stats = AutomatonStats(
            automaton_id=self._next_id,
            parent_id=parent_id,
            birth_tick=birth_tick,
            last_report_tick=birth_tick
        )
        self._stats_map[self._next_id] = stats
        self._next_id += 1
        return stats

    def should_report(self, stats: AutomatonStats, current_tick: int) -> bool:
        """Sprawdza czy należy raportować statystyki."""
        if STATS_REPORT_INTERVAL <= 0:
            return False

        ticks_since_last = current_tick - stats.last_report_tick
        return ticks_since_last >= STATS_REPORT_INTERVAL

    def report(self, stats: AutomatonStats, current_tick: int, reason: str = "periodic"):
        """Raportuje statystyki automatu."""
        report_str = stats.format_report(current_tick, reason)
        logger.info(report_str)

        # Zapisz do historii
        report_data = stats.to_dict(current_tick)
        report_data['reason'] = reason
        report_data['report_tick'] = current_tick
        # Dodajemy lineage fitness do raportu danych
        report_data['lineage_fitness'] = self.calculate_lineage_fitness(stats.automaton_id)
        
        self._all_reports.append(report_data)

        # Aktualizuj tick ostatniego raportu
        stats.last_report_tick = current_tick
    
    def calculate_lineage_fitness(self, root_id: int) -> int:
        """
        Oblicza sumaryczną ilość przetworzonego złota przez osobnika i wszystkich jego potomków.
        """
        total_gold = 0
        
        if root_id not in self._stats_map:
            return 0
            
        # Złoto tego osobnika
        total_gold += self._stats_map[root_id].gold_processed
        
        # Znajdź bezpośrednie dzieci
        children_ids = [
            sid for sid, s in self._stats_map.items() 
            if s.parent_id == root_id
        ]
        
        # Rekurencyjnie dodaj złoto potomków
        for child_id in children_ids:
            total_gold += self.calculate_lineage_fitness(child_id)
            
        return total_gold

    def get_all_reports(self) -> list[dict]:
        """Zwraca wszystkie zebrane raporty."""
        return self._all_reports.copy()

    def get_summary(self) -> dict:
        """Zwraca podsumowanie wszystkich raportów."""
        if not self._all_reports:
            return {}

        death_reports = [r for r in self._all_reports if r['reason'] == 'death']

        if not death_reports:
            return {'total_reports': len(self._all_reports)}

        return {
            'total_automata_died': len(death_reports),
            'avg_lifetime': sum(r['lifetime'] for r in death_reports) / len(death_reports),
            'avg_steps': sum(r['steps_executed'] for r in death_reports) / len(death_reports),
            'avg_distance': sum(r['distance_traveled'] for r in death_reports) / len(death_reports),
            'avg_offspring': sum(r['offspring_count'] for r in death_reports) / len(death_reports),
            'total_gold_processed': sum(r.get('gold_processed', 0) for r in death_reports),
        }


# Globalny manager statystyk
stats_manager = StatsManager()


def setup_stats_logging(level: int = logging.INFO):
    """Konfiguruje logowanie statystyk."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.setLevel(level)
