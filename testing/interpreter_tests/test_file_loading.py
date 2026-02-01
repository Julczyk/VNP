"""
Test 5: Wczytywanie programu z pliku .srl
==========================================
Testuje funkcjonalność importu programów z plików .srl.

Wczytuje przykładowy program z examples/basic_gatherer.srl
i uruchamia go w symulacji.

Oczekiwane zachowanie:
- Program wczytuje się poprawnie
- Automat wykonuje program z pliku
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from srapl_interpreter import SRAPLInterpreter, setup_logging
import logging
import arcade

from visual import WorldView

setup_logging(logging.INFO)

# Ścieżka do pliku .srl
SRL_FILE = Path(__file__).parent.parent.parent / 'examples' / 'basic_gatherer.srl'


def main():
    print("=" * 50)
    print("TEST: Wczytywanie z pliku .srl")
    print("=" * 50)

    # Sprawdź czy plik istnieje
    if not SRL_FILE.exists():
        print(f"BŁĄD: Plik nie istnieje: {SRL_FILE}")
        return

    print(f"Wczytywanie programu z: {SRL_FILE}")

    # Wczytaj program
    program_code = SRAPLInterpreter.load_program(str(SRL_FILE))
    print(f"Wczytano {len(program_code)} znaków")

    # Sparsuj skale części
    scales = SRAPLInterpreter.parse_parts_specs(program_code)
    print(f"Skale części z pliku: {scales}")

    print("")
    print("Zawartość programu:")
    print("-" * 40)
    print(program_code[:500] + "..." if len(program_code) > 500 else program_code)
    print("-" * 40)
    print("")

    # Genom zgodny z liczbą części w pliku
    genome = [
        (Engine, scales[0] if len(scales) > 0 else 1.0),
        (Scanner, scales[1] if len(scales) > 1 else 1.0),
        (Storage, scales[2] if len(scales) > 2 else 1.0),
        (Collector, scales[3] if len(scales) > 3 else 1.0),
        (Smelter, scales[4] if len(scales) > 4 else 0.5),
        (Assembler, scales[5] if len(scales) > 5 else 0.5),
        (PowerGenerator, scales[6] if len(scales) > 6 else 1.5),
    ]

    world = World(60, 60, seed=42)

    automaton = Automaton(
        program_code=program_code,
        parts_genome=genome,
        world=world,
        position=(30, 30),
        debug_interpreter=True
    )

    world.add_automaton(automaton)

    print("Uruchamianie symulacji...")
    print("=" * 50)

    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
