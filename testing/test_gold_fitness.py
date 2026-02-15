"""Test Gold Processing and Lineage Fitness."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, PowerGenerator
from config import ResourceType, FunctionID
from stats import setup_stats_logging, stats_manager
import logging

setup_stats_logging(logging.INFO)

# Minimalny program - będzie nadpisywany ręcznie lub ignorowany w teście manualnym
PROGRAM = '''
$PARTS: 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0;
$PROGRAMM
f_0();
'''

# Genom z Hutą (Smelter)
genome = [
    (Engine, 1.0),
    (Scanner, 1.0),
    (Storage, 1.0),
    (Collector, 1.0),
    (Smelter, 1.0),
    (PowerGenerator, 1.0)
]

print("=== TEST GOLD FITNESS & LINEAGE ===")

world = World(20, 20, seed=1)

# --- 1. Parent Automaton ---
print("\\nCreating Parent Automaton...")
parent = Automaton(PROGRAM, genome, world, (10, 10))
world.add_automaton(parent)
print(f"Parent ID: {parent.stats.automaton_id}")

# Daj mu złoto do magazynu
storage = parent.get_storage_parts()[0]
storage.contents[ResourceType.GOLD] = 10
print(f"Added 10 GOLD to Parent storage.")

# Uruchom Hute (f_4) ręcznie
# args=[5] -> przetwórz 5 jednostek
smelter = parent.part_map[FunctionID.SMELT]
print("Executing Smelt(5) on Parent...")
success = smelter.execute_action(parent, [5.0])

if success:
    print("Smelt action successful.")
else:
    print("Smelt action FAILED.")

# Sprawdź wyniki rodzica
print(f"Parent Gold Processed: {parent.stats.gold_processed}")
print(f"Parent Fitness: {parent.stats.calculate_fitness()}")
assert parent.stats.gold_processed == 5, "Parent should have processed 5 gold"
assert parent.stats.calculate_fitness() == 5.0, "Fitness should equal gold processed"

# --- 2. Child Automaton (Lineage) ---
print("\\nCreating Child Automaton (simulating reproduction)...")
# Symulujemy reprodukcję przekazując parent_id
child = Automaton(PROGRAM, genome, world, (11, 11), parent_id=parent.stats.automaton_id)
world.add_automaton(child)
print(f"Child ID: {child.stats.automaton_id}, Parent ID: {child.stats.parent_id}")

# Daj dziecku złoto
child_storage = child.get_storage_parts()[0]
child_storage.contents[ResourceType.GOLD] = 20
print(f"Added 20 GOLD to Child storage.")

# Dziecko przetwarza złoto
child_smelter = child.part_map[FunctionID.SMELT]
print("Executing Smelt(20) on Child...")
child_smelter.execute_action(child, [20.0])

# Sprawdź wyniki dziecka
print(f"Child Gold Processed: {child.stats.gold_processed}")
assert child.stats.gold_processed == 20, "Child should have processed 20 gold"

# --- 3. Lineage Fitness Check ---
print("\\nChecking Lineage Fitness...")
# Lineage fitness rodzica powinno wynosić: jego złoto (5) + złoto dziecka (20) = 25
parent_lineage = stats_manager.calculate_lineage_fitness(parent.stats.automaton_id)
print(f"Parent Lineage Fitness: {parent_lineage}")

if parent_lineage == 25:
    print("SUCCESS: Lineage calculation is correct (5 + 20 = 25).")
else:
    print(f"FAILURE: Expected 25, got {parent_lineage}")

assert parent_lineage == 25, "Lineage fitness calculation incorrect"

print("\\n=== TEST ZAKOŃCZONY SUKCESEM ===")
