"""
Test: Pełny cykl życia
=======================
Automat z zbalansowanym programem umożliwiającym:
- Przetrwanie (zarządzanie energią)
- Zbieranie zasobów
- Reprodukcję
- Wzrost populacji

Oczekiwane zachowanie:
- Populacja rośnie z czasem
- Automaty rozprzestrzeniają się po mapie
- Niektóre umierają, inne się rozmnażają
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

setup_logging(logging.WARNING)  # Mniej logów dla czytelności

PROGRAM_LIFECYCLE = '''
$PARTS:
1.2, 1.5, 2.0, 1.8, 0.0, 0.0, 2.5;

$PROGRAMM
# ===========================================
# LIFECYCLE - Pełny cykl życia
# ===========================================
# Zbalansowany program: przetrwanie + zbieranie + reprodukcja
#
# X[0] = kierunek (skaner)
# X[1] = odległość (skaner)

# Główna pętla: skanuj -> symulacja obsługuje resztę
f_2(1.0, 1.0);
'''


def main():
    print("=" * 50)
    print("TEST: Pełny cykl życia")
    print("=" * 50)
    print("Symulacja pełnego cyklu życia automatów.")
    print("")
    print("Obserwuj:")
    print("  - Wzrost populacji (HUD: Automata)")
    print("  - Rozprzestrzenianie się po mapie")
    print("  - Kolory: cyan=młody, zielony=zdrowy, czerwony=słaby")
    print("  - Żółty=właśnie zebrał zasoby")
    print("=" * 50)

    genome = [
        (Engine, 1.2),
        (Scanner, 1.5),
        (Storage, 2.0),
        (Collector, 1.8),
        (Smelter, 0.0),
        (Assembler, 0.0),
        (PowerGenerator, 2.5),
    ]

    world = World(100, 100, seed=42)

    # Startowy automat
    automaton = Automaton(
        program_code=PROGRAM_LIFECYCLE,
        parts_genome=genome,
        world=world,
        position=(50, 50),
        debug_interpreter=False
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
