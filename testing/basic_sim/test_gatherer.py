"""
Test: Zbieracz zasobów
=======================
Automat aktywnie zbierający zasoby.

Strategia:
1. Skanuj otoczenie
2. Idź w kierunku zasobu
3. Zbieraj
4. Powtarzaj

Oczekiwane zachowanie:
- Automat gromadzi zasoby w magazynie
- Żółte podświetlenie przy zbieraniu
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

setup_logging(logging.INFO)

PROGRAM_GATHERER = '''
$PARTS:
1.5, 2.0, 3.0, 2.0, 0.0, 0.0, 2.0;

$PROGRAMM
# ===========================================
# GATHERER - Aktywny zbieracz
# ===========================================
# X[0] = kierunek do zasobu
# X[1] = odległość do zasobu
# X[5] = licznik cykli zbierania

# Cykl: skanuj -> (ruch jest automatyczny po skanie) -> zbieraj
X[5] = X[5] + 1.0;

# Skanuj - wynik w X[0] (dir) i X[1] (dist)
f_2(1.0, 1.0);
'''


def main():
    print("=" * 50)
    print("TEST: Zbieracz zasobów")
    print("=" * 50)
    print("Automat aktywnie zbierający zasoby.")
    print("Obserwuj:")
    print("  - Żółte podświetlenie = zbieranie")
    print("  - Logi Storage w konsoli")
    print("=" * 50)

    genome = [
        (Engine, 1.5),
        (Scanner, 2.0),
        (Storage, 3.0),     # Duży magazyn
        (Collector, 2.0),   # Efektywny zbieracz
        (Smelter, 0.0),
        (Assembler, 0.0),
        (PowerGenerator, 2.0),
    ]

    world = World(80, 80, seed=123)

    automaton = Automaton(
        program_code=PROGRAM_GATHERER,
        parts_genome=genome,
        world=world,
        position=(40, 40),
        debug_interpreter=False
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
