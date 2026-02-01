"""
Test 3: Instrukcje REDO i RESTART
==================================
Testuje działanie instrukcji sterujących przepływem:
- REDO: powrót do początku bieżącego bloku
- RESTART: powrót do początku programu

Program używa liczników do kontroli liczby powtórzeń.

Oczekiwane zachowanie:
- Blok z REDO powtarza się 3 razy (X[1] = 0, 1, 2)
- Po 3 powtórzeniach następuje skanowanie
- RESTART resetuje cały program
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, PowerGenerator
from srapl_interpreter import setup_logging
import logging
import arcade

from visual import WorldView

setup_logging(logging.DEBUG)

PROGRAM = '''
$PARTS:
1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 2.0;

$PROGRAMM
# ===========================================
# TEST: REDO i RESTART
# ===========================================
# X[0] = główny licznik (ile razy program się zrestartował)
# X[1] = licznik REDO w bloku
# X[2] = limit REDO (3)

# Inicjalizacja limitu
X[2] = 3.0;

# Zwiększ główny licznik
X[0] = X[0] + 1.0;

# Blok z REDO
{
    # Zwiększ licznik REDO
    X[1] = X[1] + 1.0;

    # Jeśli licznik < limit -> REDO (powtórz blok)
    IF (X[2] - X[1]) {
        REDO;
    }
}

# Po wyjściu z bloku REDO - resetuj licznik dla następnego cyklu
X[1] = 0.0;

# Wykonaj skanowanie
f_2(1.0, 1.0);
'''

def main():
    print("=" * 50)
    print("TEST: REDO i RESTART")
    print("=" * 50)
    print("Program testuje instrukcje REDO i RESTART.")
    print("")
    print("Struktura programu:")
    print("  1. Zwiększ X[0] (licznik restartów)")
    print("  2. Blok z REDO:")
    print("     - Zwiększ X[1] (licznik REDO)")
    print("     - Jeśli X[1] < 3: REDO")
    print("  3. Po 3 REDO: skanuj (f_2)")
    print("  4. Program się kończy i restartuje")
    print("")
    print("Obserwuj logi DEBUG:")
    print("  - 'REDO signal caught' - gdy REDO jest wykonywane")
    print("  - 'Block START/END' - początki i końce bloków")
    print("  - X[1] powinno rosnąć: 1, 2, 3, potem 0")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.0),
        (Collector, 1.0),
        (PowerGenerator, 2.0),
    ]

    world = World(40, 40, seed=456)

    automaton = Automaton(
        program_code=PROGRAM,
        parts_genome=genome,
        world=world,
        position=(20, 20),
        debug_interpreter=True
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
