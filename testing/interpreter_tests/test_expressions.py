"""
Test 7: Wyrażenia matematyczne
===============================
Testuje ewaluację wyrażeń matematycznych:
- Operatory: +, -, *, /, **
- Nawiasy
- Odwołania do pamięci X[i]
- Zagnieżdżone wyrażenia

Oczekiwane zachowanie:
- Wartości w pamięci są poprawnie obliczane
- Wyrażenia w argumentach funkcji działają
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
# TEST: Wyrażenia matematyczne
# ===========================================

# Podstawowe operacje
X[0] = 10.0;
X[1] = 3.0;

# Dodawanie: 10 + 3 = 13
X[2] = X[0] + X[1];

# Odejmowanie: 10 - 3 = 7
X[3] = X[0] - X[1];

# Mnożenie: 10 * 3 = 30
X[4] = X[0] * X[1];

# Dzielenie: 10 / 3 = 3.33...
X[5] = X[0] / X[1];

# Potęgowanie: 10 ** 2 = 100
X[6] = X[0] ** 2.0;

# Złożone wyrażenie: (10 + 3) * 2 - 5 = 21
X[7] = (X[0] + X[1]) * 2.0 - 5.0;

# Zagnieżdżone nawiasy: ((10 - 3) * 2) / 7 = 2
X[8] = ((X[0] - X[1]) * 2.0) / 7.0;

# Wyrażenie z wieloma zmiennymi: X[2] + X[3] + X[4] = 13 + 7 + 30 = 50
X[9] = X[2] + X[3] + X[4];

# Test argumentów funkcji z wyrażeniami
# f_2 z argumentem (X[0] / 10) = 1.0
f_2(X[0] / 10.0, 1.0);
'''

def main():
    print("=" * 50)
    print("TEST: Wyrażenia matematyczne")
    print("=" * 50)
    print("Program testuje operacje matematyczne.")
    print("")
    print("Oczekiwane wartości po wykonaniu:")
    print("  X[0] = 10.0")
    print("  X[1] = 3.0")
    print("  X[2] = 13.0  (10 + 3)")
    print("  X[3] = 7.0   (10 - 3)")
    print("  X[4] = 30.0  (10 * 3)")
    print("  X[5] = 3.33  (10 / 3)")
    print("  X[6] = 100.0 (10 ** 2)")
    print("  X[7] = 21.0  ((10+3)*2-5)")
    print("  X[8] = 2.0   (((10-3)*2)/7)")
    print("  X[9] = 50.0  (13+7+30)")
    print("")
    print("Obserwuj logi DEBUG - przypisania i wartości.")
    print("=" * 50)

    genome = [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.0),
        (Collector, 1.0),
        (PowerGenerator, 2.0),
    ]

    world = World(40, 40, seed=42)

    automaton = Automaton(
        program_code=PROGRAM,
        parts_genome=genome,
        world=world,
        position=(20, 20),
        debug_interpreter=True
    )

    world.add_automaton(automaton)

    # Wyświetl pamięć po pierwszym kroku
    def check_memory():
        print("\n" + "=" * 50)
        print("SPRAWDZENIE PAMIĘCI (po pierwszym kroku):")
        print("=" * 50)
        for i in range(10):
            print(f"  X[{i}] = {automaton.memory[i]}")
        print("=" * 50 + "\n")

    # Hook do sprawdzenia po pierwszym update
    original_update = world.update
    first_run = [True]

    def patched_update():
        original_update()
        if first_run[0]:
            check_memory()
            first_run[0] = False

    world.update = patched_update

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
