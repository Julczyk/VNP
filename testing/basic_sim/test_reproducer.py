"""
Test: Reprodukcja
==================
Automat zbierający zasoby w celu reprodukcji.

Wymagania reprodukcji (z automaton.py):
- 5 jednostek RAW_ORE w magazynie
- >= 20 ticków od narodzin
- Energia >= 10
- Mniej niż 6 automatów w okolicy

Strategia:
1. Skanuj i zbieraj RAW_ORE
2. Po zebraniu wystarczającej ilości - reprodukcja automatyczna

Oczekiwane zachowanie:
- Automat zbiera zasoby
- Po ~20 tickach i zebraniu 5 RAW_ORE - pojawia się potomek (cyan)
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

PROGRAM_REPRODUCER = '''
$PARTS:
1.0, 1.5, 2.5, 2.0, 0.0, 0.0, 2.5;

$PROGRAMM
# ===========================================
# REPRODUCER - Zbieranie dla reprodukcji
# ===========================================
# Cel: zebrać 5 RAW_ORE, przeżyć 20 ticków
#
# X[0] = kierunek
# X[1] = odległość
# X[10] = licznik ticków

X[10] = X[10] + 1.0;

# Prosta strategia: skanuj, ruch/zbieranie obsługiwane przez symulację
f_2(1.0, 1.0);
'''


def main():
    print("=" * 50)
    print("TEST: Reprodukcja")
    print("=" * 50)
    print("Automat próbujący się rozmnożyć.")
    print("")
    print("Wymagania reprodukcji:")
    print("  - 5x RAW_ORE w magazynie")
    print("  - >= 20 ticków życia")
    print("  - Energia >= 10")
    print("")
    print("Obserwuj:")
    print("  - Logi 'can_reproduce' w konsoli")
    print("  - Nowe automaty (kolor cyan)")
    print("  - Liczba automatów w HUD")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.5),
        (Storage, 2.5),
        (Collector, 2.0),
        (Smelter, 0.0),
        (Assembler, 0.0),
        (PowerGenerator, 2.5),
    ]

    # Mały świat z dużą ilością zasobów
    world = World(60, 60, seed=42)

    automaton = Automaton(
        program_code=PROGRAM_REPRODUCER,
        parts_genome=genome,
        world=world,
        position=(30, 30),
        debug_interpreter=False
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
