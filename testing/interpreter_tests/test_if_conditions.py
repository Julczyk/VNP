"""
Test 2: Instrukcje warunkowe IF
================================
Testuje działanie instrukcji IF z różnymi warunkami.

Program sprawdza wartość X[0] i wykonuje różne akcje:
- X[0] > 50: ruch
- X[0] <= 50: odpoczynek (IDLE)

Oczekiwane zachowanie:
- Na początku X[0] = 100, więc automat się porusza
- Energia spada, gdy X[0] (ustawiane ręcznie) spadnie poniżej 50 -> IDLE
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
1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 3.0;

$PROGRAMM
# ===========================================
# TEST: Instrukcje warunkowe IF
# ===========================================
# X[0] = symulowana energia (ustawiamy ręcznie)
# X[10] = licznik kroków

# Inicjalizacja - ustaw "energię" na 100
X[0] = 100.0;

# Zwiększ licznik kroków
X[10] = X[10] + 1.0;

# Zmniejsz symulowaną energię o 5 co krok
X[0] = X[0] - 5.0;

# Warunek: jeśli energia > 50 -> skanuj
IF (X[0] - 50.0) {
    # Energia wysoka - skanuj
    f_2(1.0, 1.0);
}

# Jeśli dotarliśmy tutaj, energia <= 50 -> odpoczywaj
f_0();
'''

def main():
    print("=" * 50)
    print("TEST: Instrukcje warunkowe IF")
    print("=" * 50)
    print("Program testuje warunki IF.")
    print("X[0] zaczyna od 100 i maleje o 5 co krok.")
    print("Gdy X[0] > 50: skanowanie (f_2)")
    print("Gdy X[0] <= 50: odpoczynek (f_0)")
    print("")
    print("Obserwuj logi DEBUG - powinny pokazywać:")
    print("  - Przypisania X[0], X[10]")
    print("  - Warunki IF z wynikiem TRUE/FALSE")
    print("  - Zmianę z f_2 na f_0 po spadku energii")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.0),
        (Collector, 1.0),
        (PowerGenerator, 3.0),
    ]

    world = World(40, 40, seed=123)

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
