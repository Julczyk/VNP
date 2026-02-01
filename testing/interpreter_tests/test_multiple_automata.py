"""
Test 6: Wiele automatów z różnymi programami
=============================================
Testuje działanie wielu automatów jednocześnie,
każdy z innym programem SRAPL.

Automaty:
1. Zbieracz - skupia się na zbieraniu zasobów
2. Skaner - tylko skanuje
3. Leniwy - głównie odpoczywa

Oczekiwane zachowanie:
- Każdy automat wykonuje swój program niezależnie
- Różne zachowania są widoczne na ekranie
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

setup_logging(logging.INFO)

# Program 1: Zbieracz - skanuje i zbiera
PROGRAM_COLLECTOR = '''
$PARTS:
1.0, 1.5, 3.0, 2.0, 0.0, 0.0, 1.0;

$PROGRAMM
# ZBIERACZ - skanuje i zbiera zasoby
X[10] = X[10] + 1.0;
f_2(1.0, 1.0);
'''

# Program 2: Skaner - tylko skanuje
PROGRAM_SCANNER = '''
$PARTS:
0.5, 3.0, 1.0, 0.5, 0.0, 0.0, 1.0;

$PROGRAMM
# SKANER - ciągle skanuje otoczenie
f_2(2.0, 1.0);
'''

# Program 3: Leniwy - głównie odpoczywa
PROGRAM_LAZY = '''
$PARTS:
0.5, 0.5, 1.0, 0.5, 0.0, 0.0, 5.0;

$PROGRAMM
# LENIWY - odpoczywa, czasem skanuje
X[0] = X[0] + 1.0;

# Co 5 kroków - skanuj
IF (X[0] - 5.0) {
    X[0] = 0.0;
    f_2(1.0, 1.0);
}

# W przeciwnym razie - odpoczywaj
f_0();
'''


def main():
    print("=" * 50)
    print("TEST: Wiele automatów z różnymi programami")
    print("=" * 50)
    print("Trzy automaty z różnymi strategiami:")
    print("  1. ZBIERACZ (zielony start) - skanuje i zbiera")
    print("  2. SKANER (środek) - ciągle skanuje")
    print("  3. LENIWY (prawy) - głównie odpoczywa")
    print("")
    print("Obserwuj różnice w zachowaniu i zużyciu energii.")
    print("=" * 50)

    world = World(80, 80, seed=42)

    # Genom dla zbieracza
    genome_collector = [
        (Engine, 1.0),
        (Scanner, 1.5),
        (Storage, 3.0),
        (Collector, 2.0),
        (PowerGenerator, 1.0),
    ]

    # Genom dla skanera
    genome_scanner = [
        (Engine, 0.5),
        (Scanner, 3.0),
        (Storage, 1.0),
        (Collector, 0.5),
        (PowerGenerator, 1.0),
    ]

    # Genom dla leniwego
    genome_lazy = [
        (Engine, 0.5),
        (Scanner, 0.5),
        (Storage, 1.0),
        (Collector, 0.5),
        (PowerGenerator, 5.0),
    ]

    # Tworzenie automatów
    automaton1 = Automaton(
        program_code=PROGRAM_COLLECTOR,
        parts_genome=genome_collector,
        world=world,
        position=(20, 40),
        debug_interpreter=False
    )

    automaton2 = Automaton(
        program_code=PROGRAM_SCANNER,
        parts_genome=genome_scanner,
        world=world,
        position=(40, 40),
        debug_interpreter=False
    )

    automaton3 = Automaton(
        program_code=PROGRAM_LAZY,
        parts_genome=genome_lazy,
        world=world,
        position=(60, 40),
        debug_interpreter=False
    )

    world.add_automaton(automaton1)
    world.add_automaton(automaton2)
    world.add_automaton(automaton3)

    print(f"Utworzono {len(world.automata)} automatów")

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
