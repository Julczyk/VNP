"""
Test: Ekosystem
================
Wiele automatów startowych w różnych lokalizacjach.
Symulacja "ekosystemu" z konkurencją o zasoby.

Oczekiwane zachowanie:
- Automaty konkurują o zasoby
- Populacja rośnie, potem stabilizuje się
- Widoczna dynamika populacji
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from srapl_interpreter import setup_logging
import logging
import arcade

from visual import WorldView

setup_logging(logging.WARNING)

PROGRAM = '''
$PARTS:
1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 1.0;

$PROGRAMM
f_2(1.0, 1.0); # Skanuj

IF (X[1]) {
    f_1(X[0], 1.0); # Idź do zasobu
    f_7(1.0);       # Zbierz
}
# Jeśli X[1] == 0 (brak zasobów), wykonaj losowy ruch
IF (1.0 - X[1]) {
    f_1(2.0, 1.0); # Wykonaj ruch w losowym kierunku (np. ID 2), by szukać dalej
}

# Jeśli nie ma zasobów LUB robot jest zmęczony:
f_0();
'''

def main():
    print("=" * 50)
    print("TEST: Ekosystem")
    print("=" * 50)
    print("Symulacja ekosystemu z wieloma automatami.")
    print("Start: 5 automatów w różnych lokalizacjach")
    print("")
    print("Obserwuj:")
    print("  - Konkurencję o zasoby")
    print("  - Dynamikę populacji")
    print("  - Rozprzestrzenianie się")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.5),
        (Storage, 2.0),
        (Collector, 1.5),
        (Smelter, 0.0),
        (Assembler, 0.0),
        (PowerGenerator, 2.0),
    ]

    world = World(120, 120, seed=42)

    # 5 automatów startowych w różnych miejscach
    positions = [
        (30, 30),
        (90, 30),
        (60, 60),
        (30, 90),
        (90, 90),
    ]

    for pos in positions:
        automaton = Automaton(
            program_code=PROGRAM,
            parts_genome=genome,
            world=world,
            position=pos,
            debug_interpreter=False
        )
        world.add_automaton(automaton)

    print(f"Utworzono {len(world.automata)} automatów")

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
