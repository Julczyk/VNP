"""
Test: Przetrwanie
==================
Automat skupiony na przetrwaniu - zarządza energią i zbiera zasoby.

Strategia:
1. Gdy energia niska (< 40) -> odpoczywaj (ładuj energię)
2. Gdy energia wysoka -> skanuj, idź do zasobów, zbieraj

Oczekiwane zachowanie:
- Automat utrzymuje się przy życiu przez długi czas
- Energia oscyluje między ~40 a ~100
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

PROGRAM_SURVIVOR = '''
$PARTS:
1.0, 1.5, 2.0, 1.5, 0.0, 0.0, 3.0;

$PROGRAMM
# ===========================================
# SURVIVOR - Program przetrwania
# ===========================================
# X[0] = kierunek (wynik skanera)
# X[1] = odległość (wynik skanera)
# X[10] = próg niskiej energii
# X[11] = licznik kroków

# Inicjalizacja progu
X[10] = 40.0;
X[11] = X[11] + 1.0;

# Skanuj w poszukiwaniu zasobów
f_2(1.0, 1.0);
'''


def main():
    print("=" * 50)
    print("TEST: Przetrwanie")
    print("=" * 50)
    print("Automat z programem przetrwania.")
    print("Obserwuj:")
    print("  - Kolor automatu (zielony=energia, czerwony=mało)")
    print("  - Czy automat przeżywa przez dłuższy czas")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.5),
        (Storage, 2.0),
        (Collector, 1.5),
        (Smelter, 0.0),
        (Assembler, 0.0),
        (PowerGenerator, 3.0),  # Duży generator - szybsze ładowanie
    ]

    world = World(80, 80, seed=42)

    automaton = Automaton(
        program_code=PROGRAM_SURVIVOR,
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
