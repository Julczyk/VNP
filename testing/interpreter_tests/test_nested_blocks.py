"""
Test 4: Zagnieżdżone bloki i złożona logika
============================================
Testuje zagnieżdżone bloki IF i REDO.

Struktura:
- Zewnętrzny blok z warunkiem energii
- Wewnętrzny blok z warunkiem odległości
- REDO w wewnętrznym bloku

Oczekiwane zachowanie:
- Automat podejmuje decyzje na podstawie wielu warunków
- Zagnieżdżone bloki działają poprawnie
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
1.5, 1.5, 2.0, 1.0, 0.0, 0.0, 2.0;

$PROGRAMM
# ===========================================
# TEST: Zagnieżdżone bloki
# ===========================================
# X[0] = kierunek (z skanera)
# X[1] = odległość (z skanera)
# X[5] = symulowana energia
# X[6] = próg energii
# X[7] = licznik wewnętrznego bloku

# Inicjalizacja
X[5] = 80.0;
X[6] = 30.0;
X[7] = 0.0;

# Zewnętrzny blok - sprawdzenie energii
{
    # Zmniejsz energię
    X[5] = X[5] - 2.0;

    # Jeśli energia > próg
    IF (X[5] - X[6]) {
        # Wewnętrzny blok - logika działania
        {
            X[7] = X[7] + 1.0;

            # Po 5 iteracjach - skanuj
            IF (X[7] - 5.0) {
                f_2(1.0, 1.0);
            }

            # Mniej niż 5 iteracji - powtórz blok
            IF (5.0 - X[7]) {
                REDO;
            }
        }

        # Resetuj licznik
        X[7] = 0.0;
    }
}

# Niska energia - odpoczywaj
f_0();
'''

def main():
    print("=" * 50)
    print("TEST: Zagnieżdżone bloki")
    print("=" * 50)
    print("Program testuje zagnieżdżone bloki IF i REDO.")
    print("")
    print("Struktura:")
    print("  - Zewnętrzny blok: sprawdza energię X[5]")
    print("  - Wewnętrzny blok: REDO 5 razy, potem skanuj")
    print("  - Gdy energia < 30: odpoczynek (f_0)")
    print("")
    print("Obserwuj:")
    print("  - Zagnieżdżone 'Block START/END'")
    print("  - X[7] rośnie od 0 do 5")
    print("  - Przełączanie między f_2 i f_0")
    print("=" * 50)

    genome = [
        (Engine, 1.5),
        (Scanner, 1.5),
        (Storage, 2.0),
        (Collector, 1.0),
        (PowerGenerator, 2.0),
    ]

    world = World(50, 50, seed=789)

    automaton = Automaton(
        program_code=PROGRAM,
        parts_genome=genome,
        world=world,
        position=(25, 25),
        debug_interpreter=True
    )

    world.add_automaton(automaton)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
