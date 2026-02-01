"""
Test 1: Podstawowe skanowanie i ruch
=====================================
Automat wykonuje cyklicznie: skanuj -> idź w kierunku zasobu -> zbieraj

Oczekiwane zachowanie:
- Automat porusza się w kierunku najbliższych zasobów
- Po dotarciu zbiera zasoby
- Kolor automatu zmienia się na żółty przy zbieraniu
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, PowerGenerator
from srapl_interpreter import setup_logging
import logging
import arcade

# Włącz logowanie
setup_logging(logging.INFO)

# Import wizualizacji
from visual import WorldView

PROGRAM = '''
$PARTS:
1.5, 1.0, 2.0, 1.5, 0.0, 0.0, 2.0;

$PROGRAMM
# ===========================================
# TEST: Podstawowe skanowanie i ruch
# ===========================================
# X[0] = kierunek (wynik skanera)
# X[1] = odległość (wynik skanera)

# Skanuj w poszukiwaniu zasobów
f_2(1.0, 1.0);
'''

def main():
    print("=" * 50)
    print("TEST: Podstawowe skanowanie")
    print("=" * 50)
    print("Automat będzie cyklicznie skanować otoczenie.")
    print("Obserwuj logi - powinny pokazywać wywołania f_2 (SCAN)")
    print("=" * 50)

    genome = [
        (Engine, 1.5),
        (Scanner, 1.0),
        (Storage, 2.0),
        (Collector, 1.5),
        (PowerGenerator, 2.0),
    ]

    world = World(60, 60, seed=42)

    automaton = Automaton(
        program_code=PROGRAM,
        parts_genome=genome,
        world=world,
        position=(30, 30),
        debug_interpreter=True
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
