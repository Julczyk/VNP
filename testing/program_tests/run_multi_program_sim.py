"""
Symulacja z wieloma robotami - po jednym na każdy program z folderu start_programs.

Użycie:
    python testing/program_tests/run_multi_program_sim.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from srapl_interpreter import SRAPLInterpreter
from stats import setup_stats_logging
import logging
import arcade

from visual import WorldView

# Folder z programami startowymi
PROGRAMS_DIR = Path(__file__).parent / 'start_programs'


def load_programs() -> list[tuple[str, str]]:
    """
    Wczytuje wszystkie programy .srl z folderu start_programs.

    Returns:
        Lista krotek (nazwa_programu, kod_źródłowy)
    """
    programs = []

    if not PROGRAMS_DIR.exists():
        print(f"BŁĄD: Folder {PROGRAMS_DIR} nie istnieje!")
        return programs

    for srl_file in sorted(PROGRAMS_DIR.glob('*.srl')):
        name = srl_file.stem
        code = srl_file.read_text(encoding='utf-8')
        programs.append((name, code))
        print(f"  Wczytano: {name} ({len(code)} znaków)")

    return programs


def create_genome_from_program(program_code: str) -> list:
    """
    Tworzy genom automatu na podstawie sekcji $PARTS w programie.
    """
    scales = SRAPLInterpreter.parse_parts_specs(program_code)

    # Mapowanie indeksów na klasy części
    part_classes = [
        Engine,        # 0
        Scanner,       # 1
        Storage,       # 2
        Collector,     # 3
        Smelter,       # 4
        Assembler,     # 5
        PowerGenerator # 6
    ]

    genome = []
    for i, scale in enumerate(scales):
        if i < len(part_classes):
            genome.append((part_classes[i], scale))

    return genome


def generate_positions(count: int, world_width: int, world_height: int) -> list[tuple[int, int]]:
    """
    Generuje pozycje startowe dla automatów, rozmieszczając je równomiernie.
    """
    positions = []

    # Prosty grid
    cols = int(count ** 0.5) + 1
    rows = (count + cols - 1) // cols

    margin_x = world_width // (cols + 1)
    margin_y = world_height // (rows + 1)

    for i in range(count):
        col = i % cols
        row = i // cols
        x = margin_x * (col + 1)
        y = margin_y * (row + 1)
        positions.append((x, y))

    return positions[:count]


def main():
    print("=" * 60)
    print("SYMULACJA WIELU PROGRAMÓW")
    print("=" * 60)
    print(f"Folder programów: {PROGRAMS_DIR}")
    print()

    # Wczytaj programy
    print("Wczytywanie programów:")
    programs = load_programs()

    if not programs:
        print("Brak programów do wczytania!")
        return

    print(f"\nWczytano {len(programs)} programów")
    print()

    # Utwórz świat
    world_size = max(80, len(programs) * 20)
    world = World(world_size, world_size, seed=42)

    # Generuj pozycje
    positions = generate_positions(len(programs), world_size, world_size)

    # Utwórz automaty
    print("Tworzenie automatów:")
    for i, ((name, code), position) in enumerate(zip(programs, positions)):
        genome = create_genome_from_program(code)

        automaton = Automaton(
            program_code=code,
            parts_genome=genome,
            world=world,
            position=position,
            debug_interpreter=False
        )

        world.add_automaton(automaton)
        print(f"  [{i+1}] {name} @ {position}")

    print()
    print(f"Utworzono {len(world.automata)} automatów")
    print("=" * 60)
    print()
    print("Legenda kolorów:")
    print("  Cyan    - nowo narodzony (< 20 ticków)")
    print("  Żółty   - właśnie zebrał zasoby")
    print("  Zielony - wysoka energia")
    print("  Czerwony - niska energia")
    print()
    print("Uruchamianie symulacji...")

    # Uruchom wizualizację
    window = WorldView(world)
    arcade.run()


if __name__ == "__main__":
    main()
