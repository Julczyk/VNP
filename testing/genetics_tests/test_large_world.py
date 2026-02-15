"""
Test 3: Symulacja w dużym świecie z ograniczonymi zasobami.

Duży świat (150x150) z tylko RAW_ORE + GOLD i wyższymi progami generacji.
Ten sam format raportowania co Test 2.

Użycie:
    python testing/genetics_tests/test_large_world.py -i program.srl -t 1000
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

# Nadpisz konfigurację PRZED importem World
import config

# Ograniczone zasoby: tylko RAW_ORE i GOLD, wyższe progi
SPARSE_RESOURCE_GENERATION = {
    config.ResourceType.RAW_ORE: {
        "weight": 70,
        "amount": (3, 10),
    },
    config.ResourceType.GOLD: {
        "weight": 30,
        "amount": (1, 3),
    },
}

SPARSE_RESOURCE_THRESHOLD = {
    config.ResourceType.RAW_ORE: 0.70,  # Wyższy próg = rzadsze zasoby
    config.ResourceType.GOLD: 0.85,
}

# Nadpisz globalne konfiguracje
config.RESOURCE_GENERATION = SPARSE_RESOURCE_GENERATION
config.RESOURCE_THRESHOLD = SPARSE_RESOURCE_THRESHOLD

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from srapl_interpreter import SRAPLInterpreter
from config import ResourceType


def create_genome_from_program(program_code: str) -> list:
    """Tworzy genom automatu na podstawie sekcji $PARTS w programie."""
    scales = SRAPLInterpreter.parse_parts_specs(program_code)

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


def generate_positions(count: int, world_width: int, world_height: int) -> list:
    """Generuje pozycje startowe dla automatów."""
    positions = []
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


def collect_automaton_stats(automaton, world):
    """Zbiera statystyki dla pojedynczego automatu."""
    stats = {
        'alive': automaton.alive,
        'energy': automaton.energy,
        'position': automaton.position,
        'children': automaton.children_count,
        'age': world.tick - automaton.birth_tick,
        'gold': 0,
        'raw_ore': 0,
        'total_resources': 0,
    }

    for storage in automaton.get_storage_parts():
        for res, amt in storage.contents.items():
            stats['total_resources'] += amt
            if res == ResourceType.GOLD:
                stats['gold'] += amt
            elif res == ResourceType.RAW_ORE:
                stats['raw_ore'] += amt

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Symulacja w dużym świecie z ograniczonymi zasobami'
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Ścieżka do pliku .srl z programem'
    )
    parser.add_argument(
        '-t', '--ticks',
        type=int,
        default=1000,
        help='Liczba ticków symulacji (domyślnie: 1000)'
    )
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=5,
        help='Początkowa liczba robotów (domyślnie: 5)'
    )
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=42,
        help='Seed generatora świata (domyślnie: 42)'
    )
    parser.add_argument(
        '-w', '--world-size',
        type=int,
        default=150,
        help='Rozmiar świata (domyślnie: 150)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Wyłącz logi ticków'
    )

    args = parser.parse_args()

    # Wczytaj program
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"BŁĄD: Plik {input_path} nie istnieje!")
        sys.exit(1)

    program_code = input_path.read_text(encoding='utf-8')

    print("=" * 70)
    print("SYMULACJA W DUŻYM ŚWIECIE Z OGRANICZONYMI ZASOBAMI")
    print("=" * 70)
    print(f"Program: {input_path.name}")
    print(f"Świat: {args.world_size}x{args.world_size}, seed={args.seed}")
    print(f"Symulacja: {args.ticks} ticków, {args.count} robotów startowych")
    print()
    print("Ograniczenia zasobów:")
    print(f"  - Tylko RAW_ORE i GOLD")
    print(f"  - RAW_ORE próg: 0.70 (rzadsze)")
    print(f"  - GOLD próg: 0.85 (bardzo rzadkie)")
    print()

    # Utwórz świat
    world = World(args.world_size, args.world_size, seed=args.seed)

    # Policz zasoby na mapie
    resource_count = {ResourceType.RAW_ORE: 0, ResourceType.GOLD: 0}
    tiles_with_resources = 0

    for y in range(args.world_size):
        for x in range(args.world_size):
            tile = world.get_tile((x, y))
            if tile.materials:
                tiles_with_resources += 1
                for res, amt in tile.materials.items():
                    if res in resource_count:
                        resource_count[res] += amt

    print(f"Zasoby na mapie:")
    print(f"  - Kafelków z zasobami: {tiles_with_resources}")
    print(f"  - RAW_ORE: {resource_count[ResourceType.RAW_ORE]}")
    print(f"  - GOLD: {resource_count[ResourceType.GOLD]}")
    print()

    # Generuj pozycje i automaty
    positions = generate_positions(args.count, args.world_size, args.world_size)
    genome = create_genome_from_program(program_code)

    for position in positions:
        automaton = Automaton(
            program_code=program_code,
            parts_genome=genome,
            world=world,
            position=position
        )
        world.add_automaton(automaton)

    print(f"Utworzono {len(world.automata)} automatów")
    print("Uruchamianie symulacji...")
    print()

    # Symulacja
    all_automata = list(world.automata)

    for tick in range(args.ticks):
        world.update()

        # Dodaj nowe automaty do śledzenia
        for a in world.automata:
            if a not in all_automata:
                all_automata.append(a)

        if not args.quiet and tick % 100 == 0:
            alive = len([a for a in all_automata if a.alive])
            total = len(all_automata)
            print(f"Tick {tick}: żywych={alive}, wszystkich={total}")

        # Zakończ jeśli wszyscy zginęli
        if len(world.automata) == 0:
            print(f"Wszyscy zginęli w ticku {tick}!")
            break

    # Zbierz statystyki
    print()
    print("=" * 70)
    print("WYNIKI SYMULACJI (DUŻY ŚWIAT)")
    print("=" * 70)

    final_stats = []
    for i, automaton in enumerate(all_automata):
        stats = collect_automaton_stats(automaton, world)
        stats['id'] = i
        final_stats.append(stats)

    # Statystyki ogólne
    alive_count = sum(1 for s in final_stats if s['alive'])
    total_children = sum(s['children'] for s in final_stats)
    total_gold = sum(s['gold'] for s in final_stats)

    print(f"Ticków: {world.tick}")
    print(f"Automatów całkowicie: {len(all_automata)}")
    print(f"Żywych na koniec: {alive_count}")
    print(f"Łączna liczba potomków: {total_children}")
    print(f"Łączne złoto: {total_gold}")
    print()

    # TOP 10 wg złota
    print("TOP 10 wg ZŁOTA:")
    print("-" * 50)
    by_gold = sorted(final_stats, key=lambda x: x['gold'], reverse=True)[:10]
    for rank, s in enumerate(by_gold, 1):
        status = "ŻYWY" if s['alive'] else "MARTWY"
        print(f"  {rank}. Robot #{s['id']}: gold={s['gold']}, children={s['children']}, {status}")

    print()

    # TOP 10 wg reprodukcji
    print("TOP 10 wg REPRODUKCJI:")
    print("-" * 50)
    by_children = sorted(final_stats, key=lambda x: x['children'], reverse=True)[:10]
    for rank, s in enumerate(by_children, 1):
        status = "ŻYWY" if s['alive'] else "MARTWY"
        print(f"  {rank}. Robot #{s['id']}: children={s['children']}, gold={s['gold']}, {status}")

    print()

    # Najlepsze przeżywające
    alive_stats = [s for s in final_stats if s['alive']]
    if alive_stats:
        print("NAJLEPSZE PRZEŻYWAJĄCE ROBOTY:")
        print("-" * 50)
        by_score = sorted(alive_stats, key=lambda x: x['children'] + x['gold'], reverse=True)[:10]
        for rank, s in enumerate(by_score, 1):
            print(f"  {rank}. Robot #{s['id']}: children={s['children']}, gold={s['gold']}, "
                  f"energy={s['energy']:.1f}, age={s['age']}")
    else:
        print("Brak przeżywających robotów.")

    print()
    print("Uwaga: Ten test używa ograniczonych zasobów (tylko RAW_ORE + GOLD)")
    print("z wyższymi progami generacji, co symuluje trudniejsze środowisko.")


if __name__ == "__main__":
    main()
