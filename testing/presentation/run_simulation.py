#!/usr/bin/env python3
"""
Skrypt do uruchamiania symulacji z programem SRAPL.

Uruchamia symulacje, zbiera statystyki i zapisuje wyniki.
Moze zapisywac obrazy w 100., 1000. i 10000. kroku.
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Dodaj katalog src do sciezki
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator
from srapl_interpreter import SRAPLInterpreter
from stats import stats_manager, setup_stats_logging
from config import PARTS_ORDER, get_function_to_part_map

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Kolejnosc czesci w $PARTS
PARTS_CLASSES = [Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator]


def load_program(filepath: str) -> str:
    """Wczytuje program z pliku .srl."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def build_genome(program_code: str) -> list:
    """
    Buduje genom z programu SRAPL.

    Returns:
        Lista par (PartClass, scale)
    """
    scales = SRAPLInterpreter.parse_parts_specs(program_code)

    if len(scales) != len(PARTS_CLASSES):
        logger.warning(f"Niepoprawna liczba skal: {len(scales)}, oczekiwano {len(PARTS_CLASSES)}")
        # Uzupelni domyslnymi wartosciami
        while len(scales) < len(PARTS_CLASSES):
            scales.append(1.0)

    genome = [(cls, scale) for cls, scale in zip(PARTS_CLASSES, scales)]
    return genome


def run_simulation(
    program_path: str,
    max_ticks: int = 10000,
    world_seed: int = 42,
    world_size: tuple = (80, 80),
    start_position: tuple = (15, 15),
    output_dir: str = None,
    save_images: bool = False,
    show_visualization: bool = False
) -> dict:
    """
    Uruchamia symulacje z podanym programem.

    Args:
        program_path: Sciezka do pliku .srl
        max_ticks: Maksymalna liczba krokow
        world_seed: Seed swiata
        world_size: Rozmiar swiata (width, height)
        start_position: Pozycja startowa automatu
        output_dir: Katalog na wyniki
        save_images: Czy zapisywac obrazy
        show_visualization: Czy pokazac wizualizacje na koniec

    Returns:
        Slownik z wynikami symulacji
    """
    program_name = Path(program_path).stem
    logger.info(f"=== Uruchamianie symulacji: {program_name} ===")

    # Wczytaj program
    program_code = load_program(program_path)
    genome = build_genome(program_code)

    logger.info(f"Genom: {[(cls.__name__, scale) for cls, scale in genome]}")

    # Utworz swiat
    world = World(world_size[0], world_size[1], seed=world_seed)
    logger.info(f"Swiat: {world_size[0]}x{world_size[1]}, seed={world_seed}")

    # Utworz automat
    automaton = Automaton(
        program_code=program_code,
        parts_genome=genome,
        world=world,
        position=start_position,
        debug_interpreter=False
    )
    world.add_automaton(automaton)

    # Przygotuj katalog wyjsciowy
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        log_file = output_path / f"{program_name}_log.txt"
    else:
        log_file = None

    # Przekieruj logi do pliku
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(file_handler)

    # Lista tickow do zapisania obrazow
    image_ticks = [100, 1000, 10000] if save_images else []

    # Uruchom symulacje
    logger.info(f"Start symulacji, max_ticks={max_ticks}")
    start_time = datetime.now()

    results = {
        'program': program_name,
        'world_seed': world_seed,
        'world_size': world_size,
        'start_position': start_position,
        'max_ticks': max_ticks,
        'final_tick': 0,
        'automaton_died': False,
        'death_tick': None,
        'total_automata': 0,
        'final_automata_count': 0,
        'stats': None
    }

    try:
        for tick in range(max_ticks):
            world.update()

            # Loguj postep co 1000 tickow
            if tick % 1000 == 0:
                alive_count = len(world.automata)
                logger.info(f"Tick {tick}: {alive_count} automatow zyje")

            # Zapisz obraz w okreslonych momentach
            if tick + 1 in image_ticks and save_images and output_dir:
                try:
                    save_world_image(world, output_path / f"{program_name}_tick{tick+1}.png")
                except Exception as e:
                    logger.warning(f"Nie udalo sie zapisac obrazu: {e}")

            # Sprawdz czy automat zyje
            if len(world.automata) == 0:
                logger.info(f"Wszystkie automaty zginely w ticku {tick}")
                results['automaton_died'] = True
                results['death_tick'] = tick
                results['final_tick'] = tick
                break
        else:
            results['final_tick'] = max_ticks

    except KeyboardInterrupt:
        logger.info("Symulacja przerwana przez uzytkownika")
        results['final_tick'] = world.tick

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Zbierz statystyki
    results['final_automata_count'] = len(world.automata)
    results['simulation_duration_seconds'] = duration

    # Pobierz statystyki ze stats_manager
    summary = stats_manager.get_summary()
    results['stats_summary'] = summary
    all_reports = stats_manager.get_all_reports()
    results['all_reports'] = all_reports

    logger.info(f"=== Symulacja zakonczona ===")
    logger.info(f"Tick koncowy: {results['final_tick']}")
    logger.info(f"Automaty na koncu: {results['final_automata_count']}")
    logger.info(f"Czas trwania: {duration:.2f}s")

    if summary:
        logger.info(f"Podsumowanie statystyk: {summary}")

    # Zapisz wyniki do JSON
    if output_dir:
        results_file = output_path / f"{program_name}_results.json"
        # Konwertuj na serializowalne typy
        serializable_results = make_serializable(results)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        logger.info(f"Wyniki zapisane do: {results_file}")

    # Pokaz wizualizacje jesli requested
    if show_visualization and len(world.automata) > 0:
        logger.info("Uruchamianie wizualizacji...")
        show_world_visualization(world)

    return results


def make_serializable(obj):
    """Konwertuje obiekt na serializowalny do JSON."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


def save_world_image(world, filepath):
    """
    Zapisuje obraz swiata do pliku.

    Wymaga arcade - jezeli niedostepne, loguje ostrzezenie.
    """
    try:
        import arcade
        from PIL import Image
        import numpy as np

        TILE_SIZE = 10
        width = world.width * TILE_SIZE
        height = world.height * TILE_SIZE

        # Utworz obraz
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        pixels = img.load()

        # Kolory
        from config import ResourceType
        LAND_COLOR = (0, 100, 0)  # ciemna zielen
        WATER_COLOR = (0, 0, 150)
        RESOURCE_COLORS = {
            ResourceType.RAW_ORE: (139, 69, 19),  # brown
            ResourceType.COAL: (50, 30, 10),
            ResourceType.IRON: (128, 128, 128),
            ResourceType.GOLD: (255, 215, 0),
            ResourceType.URANIUM: (50, 205, 50),
        }

        from world.tile import WaterTile

        for y in range(world.height):
            for x in range(world.width):
                tile = world.map[y, x]

                if isinstance(tile, WaterTile):
                    color = WATER_COLOR
                else:
                    color = LAND_COLOR
                    if tile.materials:
                        res = max(tile.materials.items(), key=lambda x: x[1])[0]
                        color = RESOURCE_COLORS.get(res, LAND_COLOR)

                # Wypelnij kafelek
                for dy in range(TILE_SIZE):
                    for dx in range(TILE_SIZE):
                        px = x * TILE_SIZE + dx
                        py = (world.height - 1 - y) * TILE_SIZE + dy
                        if 0 <= px < width and 0 <= py < height:
                            pixels[px, py] = color

        # Narysuj automaty
        for automaton in world.automata:
            ax, ay = automaton.position
            center_x = ax * TILE_SIZE + TILE_SIZE // 2
            center_y = (world.height - 1 - ay) * TILE_SIZE + TILE_SIZE // 2

            # Kolor zalezny od energii
            energy_ratio = max(0.0, min(1.0, automaton.energy / automaton.max_energy))
            r = int(255 * (1 - energy_ratio))
            g = int(255 * energy_ratio)
            color = (r, g, 0)

            # Narysuj kolo (przyblizone)
            radius = TILE_SIZE // 2 - 1
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        px = center_x + dx
                        py = center_y + dy
                        if 0 <= px < width and 0 <= py < height:
                            pixels[px, py] = color

        img.save(filepath)
        logger.info(f"Zapisano obraz: {filepath}")

    except ImportError as e:
        logger.warning(f"Nie mozna zapisac obrazu (brak PIL): {e}")


def show_world_visualization(world):
    """Pokazuje wizualizacje swiata z arcade."""
    try:
        import arcade
        from visual import WorldView

        window = WorldView(world)
        arcade.run()
    except ImportError as e:
        logger.warning(f"Nie mozna uruchomic wizualizacji: {e}")


def run_strategy_tests(output_base: str = None):
    """Uruchamia testy wszystkich strategii."""
    strategies_dir = Path(__file__).parent / 'programs' / 'strategies'

    if output_base is None:
        output_base = Path(__file__).parent / 'results' / 'strategies'
    else:
        output_base = Path(output_base)

    strategies = list(strategies_dir.glob('*.srl'))

    logger.info(f"Znaleziono {len(strategies)} strategii do przetestowania")

    all_results = []
    for strategy_file in strategies:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testowanie strategii: {strategy_file.stem}")
        logger.info(f"{'='*60}")

        result = run_simulation(
            program_path=str(strategy_file),
            max_ticks=10000,
            world_seed=42,
            output_dir=str(output_base),
            save_images=True,
            show_visualization=False
        )
        all_results.append(result)

        # Reset stats manager dla nowej symulacji
        stats_manager._all_reports = []
        stats_manager._next_id = 1

    # Podsumowanie
    logger.info(f"\n{'='*60}")
    logger.info("PODSUMOWANIE STRATEGII")
    logger.info(f"{'='*60}")
    for result in all_results:
        logger.info(f"{result['program']}: tick={result['final_tick']}, automata={result['final_automata_count']}")

    return all_results


def run_scale_tests(output_base: str = None):
    """Uruchamia testy roznych skal czesci."""
    scales_dir = Path(__file__).parent / 'programs' / 'scales'

    if output_base is None:
        output_base = Path(__file__).parent / 'results' / 'scales'
    else:
        output_base = Path(output_base)

    scales = list(scales_dir.glob('*.srl'))

    logger.info(f"Znaleziono {len(scales)} konfiguracji skal do przetestowania")

    all_results = []
    for scale_file in scales:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testowanie konfiguracji: {scale_file.stem}")
        logger.info(f"{'='*60}")

        result = run_simulation(
            program_path=str(scale_file),
            max_ticks=10000,
            world_seed=42,
            output_dir=str(output_base),
            save_images=True,
            show_visualization=False
        )
        all_results.append(result)

        # Reset stats manager
        stats_manager._all_reports = []
        stats_manager._next_id = 1

    logger.info(f"\n{'='*60}")
    logger.info("PODSUMOWANIE SKAL")
    logger.info(f"{'='*60}")
    for result in all_results:
        logger.info(f"{result['program']}: tick={result['final_tick']}, automata={result['final_automata_count']}")

    return all_results


def run_world_tests(output_base: str = None):
    """Uruchamia testy z roznymi parametrami swiata."""
    # Uzyj strategii standardowej
    standard_program = Path(__file__).parent / 'programs' / 'strategies' / 'standard.srl'

    if output_base is None:
        output_base = Path(__file__).parent / 'results' / 'worlds'
    else:
        output_base = Path(output_base)

    # Rozne konfiguracje swiata
    world_configs = [
        {'name': 'small_world', 'size': (40, 40), 'seed': 42},
        {'name': 'large_world', 'size': (120, 120), 'seed': 42},
        {'name': 'seed_100', 'size': (80, 80), 'seed': 100},
        {'name': 'seed_200', 'size': (80, 80), 'seed': 200},
        {'name': 'seed_300', 'size': (80, 80), 'seed': 300},
    ]

    logger.info(f"Testowanie {len(world_configs)} konfiguracji swiata")

    all_results = []
    for config in world_configs:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testowanie swiata: {config['name']}")
        logger.info(f"{'='*60}")

        result = run_simulation(
            program_path=str(standard_program),
            max_ticks=10000,
            world_seed=config['seed'],
            world_size=config['size'],
            output_dir=str(output_base),
            save_images=True,
            show_visualization=False
        )
        # Dodaj info o konfiguracji
        result['world_config'] = config['name']
        all_results.append(result)

        # Zmien nazwe plikow wynikowych
        old_name = output_base / 'standard_results.json'
        new_name = output_base / f"{config['name']}_results.json"
        if old_name.exists():
            old_name.rename(new_name)

        # Reset stats manager
        stats_manager._all_reports = []
        stats_manager._next_id = 1

    logger.info(f"\n{'='*60}")
    logger.info("PODSUMOWANIE SWIATOW")
    logger.info(f"{'='*60}")
    for result in all_results:
        logger.info(f"{result.get('world_config', result['program'])}: tick={result['final_tick']}, automata={result['final_automata_count']}")

    return all_results


def main():
    parser = argparse.ArgumentParser(description='Uruchom symulacje VNP')
    parser.add_argument('--program', '-p', type=str, help='Sciezka do programu .srl')
    parser.add_argument('--ticks', '-t', type=int, default=10000, help='Maksymalna liczba tickow')
    parser.add_argument('--seed', '-s', type=int, default=42, help='Seed swiata')
    parser.add_argument('--output', '-o', type=str, help='Katalog wyjsciowy')
    parser.add_argument('--images', '-i', action='store_true', help='Zapisuj obrazy')
    parser.add_argument('--visualize', '-v', action='store_true', help='Pokaz wizualizacje')

    parser.add_argument('--strategies', action='store_true', help='Uruchom testy strategii (E1)')
    parser.add_argument('--scales', action='store_true', help='Uruchom testy skal (E2)')
    parser.add_argument('--worlds', action='store_true', help='Uruchom testy swiatow (E3)')
    parser.add_argument('--all', '-a', action='store_true', help='Uruchom wszystkie testy')

    args = parser.parse_args()

    if args.all:
        logger.info("=== URUCHAMIANIE WSZYSTKICH TESTOW ===")
        run_strategy_tests()
        run_scale_tests()
        run_world_tests()
    elif args.strategies:
        run_strategy_tests()
    elif args.scales:
        run_scale_tests()
    elif args.worlds:
        run_world_tests()
    elif args.program:
        run_simulation(
            program_path=args.program,
            max_ticks=args.ticks,
            world_seed=args.seed,
            output_dir=args.output,
            save_images=args.images,
            show_visualization=args.visualize
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
