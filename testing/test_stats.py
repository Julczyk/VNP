"""Test systemu statystyk."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, PowerGenerator
from stats import setup_stats_logging, stats_manager
import logging

setup_stats_logging(logging.INFO)

PROGRAM = '''
$PARTS: 1.0, 1.5, 2.0, 1.5, 0.0, 0.0, 2.0;

$PROGRAMM
f_2(1.0, 1.0);
'''

genome = [
    (Engine, 1.0),
    (Scanner, 1.5),
    (Storage, 2.0),
    (Collector, 1.5),
    (PowerGenerator, 2.0)
]

print("=== TEST SYSTEMU STATYSTYK ===")

world = World(20, 20, seed=1)
auto = Automaton(PROGRAM, genome, world, (10, 10))
world.add_automaton(auto)

print(f"Automaton stats ID: {auto.stats.automaton_id}")

# Symuluj kilka kroków
for i in range(100):
    world.update()

print(f"\nPo 5 krokach:")
print(f"  Steps executed: {auto.stats.steps_executed}")
print(f"  Distance traveled: {auto.stats.distance_traveled}")
print(f"  Energy consumed: {auto.stats.energy_consumed:.1f}")
print(f"  Energy produced: {auto.stats.energy_produced:.1f}")
print(f"  Resources collected: {auto.stats.get_total_resources_collected()}")

# Symuluj śmierć - powinna wyświetlić raport
print("\n--- Symulacja śmierci ---")
auto.energy = 0
auto.die()

# Sprawdź zebrane raporty
print("\n--- Zebrane raporty ---")
reports = stats_manager.get_all_reports()
print(f"Liczba raportów: {len(reports)}")
for r in reports:
    print(f"  ID={r['automaton_id']}, reason={r['reason']}, lifetime={r['lifetime']}, steps={r['steps_executed']}")

# Podsumowanie
print("\n--- Podsumowanie ---")
summary = stats_manager.get_summary()
for k, v in summary.items():
    print(f"  {k}: {v}")

print("\n=== TEST ZAKOŃCZONY ===")
