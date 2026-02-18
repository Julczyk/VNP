"""
Skrypt do przeprowadzania symulacji VNP (Von Neumann Probes).

Umożliwia uruchamianie symulacji ewolucji samoreplikujących się automatów
z różnymi parametrami i eksport wyników.

Użycie z linii poleceń:
    python src/Simulation.py --input_programs examples/ --time 300 --visualize
    python src/Simulation.py -i examples/ -t 500 --mutation_speed 0.2 -o results/
"""

import argparse
import logging
import os
import random
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# Dodaj ścieżkę src do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from world.world import World
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, Smelter, Assembler, PowerGenerator, GoldDepositor
from config import ResourceType, PARTS_ORDER, get_function_to_part_map
from srapl_interpreter import SRAPLInterpreter
from stats import stats_manager, AutomatonStats

logger = logging.getLogger('SIMULATION')


def get_default_genome():
    """Zwraca domyślny genom części."""
    return [
        (Engine, 1.0),
        (Scanner, 1.0),
        (Storage, 1.5),
        (Collector, 1.0),
        (Smelter, 0.5),
        (Assembler, 0.5),
        (PowerGenerator, 1.0),
        (GoldDepositor, 0.5),
    ]


def parse_genome_from_program(program_code: str) -> list:
    """
    Parsuje genom części z sekcji $PARTS programu SRAPL.

    Returns:
        Lista krotek (PartClass, scale)
    """
    scales = SRAPLInterpreter.parse_parts_specs(program_code)
    func_to_part = get_function_to_part_map()

    genome = []
    for i, fid in enumerate(PARTS_ORDER):
        if i < len(scales) and fid in func_to_part:
            part_cls = func_to_part[fid]
            genome.append((part_cls, scales[i]))

    return genome


def load_programs_from_folder(folder_path: str) -> List[Dict[str, Any]]:
    """
    Wczytuje programy SRAPL z folderu.

    Args:
        folder_path: Ścieżka do folderu z plikami .srl

    Returns:
        Lista słowników z kluczami 'program' i 'genome'
    """
    folder = Path(folder_path)
    programs = []

    if not folder.exists():
        raise FileNotFoundError(f"Folder nie istnieje: {folder_path}")

    for srl_file in sorted(folder.glob("*.srl")):
        program_code = srl_file.read_text(encoding='utf-8')
        try:
            genome = parse_genome_from_program(program_code)
            if not genome:
                genome = get_default_genome()
        except Exception:
            genome = get_default_genome()

        programs.append({
            'program': program_code,
            'genome': genome,
            'filename': srl_file.name
        })

    return programs


def calculate_start_positions(count: int, world_size: tuple, center: tuple = None) -> List[tuple]:
    """
    Oblicza pozycje startowe dla automatów w kwadracie wokół centrum mapy.

    Args:
        count: Liczba automatów
        world_size: Rozmiar świata (width, height)
        center: Opcjonalne centrum (domyślnie środek mapy)

    Returns:
        Lista pozycji (x, y)
    """
    width, height = world_size
    if center is None:
        center = (width // 2, height // 2)

    cx, cy = center

    # Oblicz rozmiar kwadratu startowego
    side = max(3, int((count ** 0.5) + 1))
    half = side // 2

    positions = []
    for i in range(count):
        # Rozłóż w kwadracie
        dx = (i % side) - half
        dy = (i // side) - half

        x = max(1, min(width - 2, cx + dx))
        y = max(1, min(height - 2, cy + dy))

        positions.append((x, y))

    return positions


def simulate(
    resources: dict = None,
    time: int = 300,
    starting_population: List[Dict] = None,
    size: List[int] = None,
    mutation_speed: float = 0,
    mutation_type: str = "",
    visualize: bool = False,
    seed: int = 42,
    return_data: str = "df",
    make_timelapse: bool = False,
    export_frames: List[int] = None,
    logging_enabled: bool = False,
    output_folder: str = None
) -> pd.DataFrame:
    """
    Przeprowadza symulację VNP.

    Args:
        resources: Progi dla zasobów (nieużywane obecnie, zarezerwowane)
        time: Liczba ticków symulacji
        starting_population: Lista automatów startowych [{'program': str, 'position': [x,y]}]
        size: Rozmiar świata [width, height]
        mutation_speed: Współczynnik mutacji (0 = brak mutacji)
        mutation_type: Typ mutacji ("disabled", "all")
        visualize: Czy pokazać wizualizację
        seed: Ziarno generatora losowego
        return_data: Format zwracanych danych ("df" = DataFrame)
        make_timelapse: Czy eksportować obrazy na każdy tick
        export_frames: Lista ticków do eksportu obrazów
        logging_enabled: Czy włączyć logowanie na stdout
        output_folder: Folder na wyniki

    Returns:
        pd.DataFrame z danymi automatów
    """
    if size is None:
        size = [80, 80]
    if starting_population is None:
        starting_population = []
    if export_frames is None:
        export_frames = []
    if resources is None:
        resources = {}

    # Konfiguracja logowania
    if logging_enabled:
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.getLogger('AUTOMATON').setLevel(logging.INFO)
    else:
        logging.getLogger('AUTOMATON').setLevel(logging.WARNING)

    # Reset managera statystyk
    stats_manager.reset()

    # Ustawienie ziarna losowego
    random.seed(seed)

    # Tworzenie świata
    world = World(size[1], size[0], seed=seed)

    # Ustawienie parametrów mutacji
    if mutation_type == "disabled" or mutation_speed == 0:
        world.mutation_rate = 0
    else:
        world.mutation_rate = mutation_speed

    # Tworzenie folderu wyjściowego
    if output_folder:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        if make_timelapse or export_frames:
            frames_path = output_path / "frames"
            frames_path.mkdir(exist_ok=True)

    # Tworzenie automatów startowych
    positions = calculate_start_positions(len(starting_population), (size[0], size[1]))

    automata_data = []  # Dane do DataFrame

    for i, automaton_spec in enumerate(starting_population):
        program = automaton_spec.get('program', '')
        pos = automaton_spec.get('position', positions[i] if i < len(positions) else (size[0]//2, size[1]//2))

        # Parsuj genom z programu lub użyj domyślnego
        if 'genome' in automaton_spec:
            genome = automaton_spec['genome']
        else:
            try:
                genome = parse_genome_from_program(program)
                if not genome:
                    genome = get_default_genome()
            except Exception:
                genome = get_default_genome()

        automaton = Automaton(
            program_code=program,
            parts_genome=genome,
            world=world,
            position=pos,
            parent_id=None
        )
        automaton.stats.start_position = pos

        world.add_automaton(automaton)

    # Funkcja do zapisu ramki
    def save_frame(tick: int, path: Path):
        try:
            import arcade
            from PIL import Image

            # Renderuj świat do obrazu
            img_width = size[0] * 5
            img_height = size[1] * 5

            img = Image.new('RGB', (img_width, img_height), (0, 100, 0))
            pixels = img.load()

            # Rysuj kafelki
            for y in range(size[1]):
                for x in range(size[0]):
                    tile = world.map[y, x]
                    from world.tile import WaterTile

                    if isinstance(tile, WaterTile):
                        color = (0, 0, 150)
                    elif tile.materials:
                        # Kolor zależny od zasobu
                        res = list(tile.materials.keys())[0]
                        color_map = {
                            ResourceType.RAW_ORE: (139, 69, 19),
                            ResourceType.COAL: (50, 50, 50),
                            ResourceType.IRON: (128, 128, 128),
                            ResourceType.GOLD: (255, 215, 0),
                            ResourceType.URANIUM: (50, 205, 50),
                        }
                        color = color_map.get(res, (0, 100, 0))
                    else:
                        color = (0, 100, 0)

                    for py in range(5):
                        for px in range(5):
                            pixels[x*5 + px, (size[1]-1-y)*5 + py] = color

            # Rysuj automaty
            for automaton in world.automata:
                ax, ay = automaton.position
                energy_ratio = automaton.energy / automaton.max_energy
                r = int(255 * (1 - energy_ratio))
                g = int(255 * energy_ratio)
                color = (r, g, 0)

                for py in range(5):
                    for px in range(5):
                        if 0 <= ax*5 + px < img_width and 0 <= (size[1]-1-ay)*5 + py < img_height:
                            pixels[ax*5 + px, (size[1]-1-ay)*5 + py] = color

            img.save(path / f"frame_{tick:05d}.png")
        except ImportError:
            pass  # PIL nie jest zainstalowany

    # Wizualizacja
    if visualize:
        try:
            import arcade
            from visual import WorldView

            # Uruchom wizualizację z automatycznym zatrzymaniem
            class SimulationView(WorldView):
                def __init__(self, world, max_ticks):
                    super().__init__(world)
                    self.max_ticks = max_ticks
                    self.simulation_done = False

                def on_update(self, delta_time):
                    if not self.paused and self.world.tick < self.max_ticks:
                        if self.tick % 5 == 0:
                            self.world.update()

                            if make_timelapse and output_folder:
                                save_frame(self.world.tick, Path(output_folder) / "frames")
                            if self.world.tick in export_frames and output_folder:
                                save_frame(self.world.tick, Path(output_folder) / "frames")

                        self.tick += 1
                    elif self.world.tick >= self.max_ticks and not self.simulation_done:
                        self.simulation_done = True
                        logger.info(f"Symulacja zakończona po {self.world.tick} tickach")

            window = SimulationView(world, time)
            arcade.run()

        except ImportError:
            logger.warning("arcade nie jest zainstalowany, uruchamiam bez wizualizacji")
            visualize = False

    # Symulacja bez wizualizacji
    if not visualize:
        for tick in range(time):
            world.update()

            if make_timelapse and output_folder:
                save_frame(world.tick, Path(output_folder) / "frames")
            if world.tick in export_frames and output_folder:
                save_frame(world.tick, Path(output_folder) / "frames")

            if logging_enabled and tick % 50 == 0:
                logger.info(f"Tick {tick}/{time}, automaty: {len(world.automata)}")

    # Zbieranie danych do DataFrame
    all_stats = []

    # Zbierz statystyki ze wszystkich automatów (żywych i martwych)
    for automaton_id, stats in stats_manager._stats_registry.items():
        # Określ czy automat żyje na końcu
        alive_at_end = any(
            a.stats.automaton_id == automaton_id and a.alive
            for a in world.automata
        )

        # Oblicz wiek
        if stats.death_tick is not None:
            age = stats.death_tick - stats.birth_tick
        else:
            age = world.tick - stats.birth_tick

        # Znajdź program automatu
        program = ""
        for a in world.automata:
            if a.stats.automaton_id == automaton_id:
                program = a.interpreter.program
                break

        record = {
            'ID': automaton_id,
            'tick': stats.birth_tick,
            'age': age,
            'program': program,
            'position': stats.start_position,
            'total_distance_traveled': round(stats.distance_traveled, 2),
            'energy_produced': round(stats.energy_produced, 2),
            'energy_consumed': round(stats.energy_consumed, 2),
            'offspring_count': stats.offspring_count,
            'alive_at_end': alive_at_end,
            'parent_ID': stats.parent_id if stats.parent_id else -1,
        }

        # Dodaj zebrane zasoby jako osobne kolumny
        for res_type in ResourceType:
            col_name = f"{res_type.name}_gathered"
            record[col_name] = stats.resources_collected.get(res_type, 0)

        all_stats.append(record)

    # Tworzenie DataFrame
    df = pd.DataFrame(all_stats)

    # Zapis wyników
    if output_folder:
        output_path = Path(output_folder)

        # Zapisz DataFrame
        df.to_csv(output_path / "results.csv", index=False)

        # Zapisz raport tekstowy
        with open(output_path / "report.txt", 'w') as f:
            f.write(f"=== RAPORT SYMULACJI VNP ===\n")
            f.write(f"Czas symulacji: {time} ticków\n")
            f.write(f"Rozmiar świata: {size[0]}x{size[1]}\n")
            f.write(f"Seed: {seed}\n")
            f.write(f"Współczynnik mutacji: {mutation_speed}\n")
            f.write(f"\n=== STATYSTYKI ===\n")
            f.write(f"Początkowa populacja: {len(starting_population)}\n")
            f.write(f"Końcowa populacja: {len(world.automata)}\n")
            f.write(f"Łączna liczba automatów: {len(df)}\n")
            f.write(f"Średni wiek: {df['age'].mean():.2f} ticków\n")
            f.write(f"Średnia liczba potomków: {df['offspring_count'].mean():.2f}\n")
            f.write(f"Średnia przebyta odległość: {df['total_distance_traveled'].mean():.2f}\n")

    if return_data == "df":
        return df
    else:
        return df


def main():
    parser = argparse.ArgumentParser(
        description='Symulacja VNP - Von Neumann Probes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-i', '--input_programs',
        type=str,
        default=None,
        help='Ścieżka do folderu z programami .srl'
    )
    parser.add_argument(
        '-t', '--time',
        type=int,
        default=300,
        help='Liczba ticków symulacji'
    )
    parser.add_argument(
        '--size',
        type=int,
        nargs=2,
        default=[80, 80],
        help='Rozmiar świata [width height]'
    )
    parser.add_argument(
        '-m', '--mutation_speed',
        type=float,
        default=0.1,
        help='Współczynnik mutacji (0 = brak mutacji)'
    )
    parser.add_argument(
        '--mutation_type',
        type=str,
        choices=['disabled', 'all'],
        default='all',
        help='Typ mutacji'
    )
    parser.add_argument(
        '-v', '--visualize',
        action='store_true',
        help='Pokaż wizualizację'
    )
    parser.add_argument(
        '-s', '--seed',
        type=int,
        default=42,
        help='Ziarno generatora losowego'
    )
    parser.add_argument(
        '-o', '--output_folder',
        type=str,
        default=None,
        help='Folder na wyniki'
    )
    parser.add_argument(
        '--make_timelapse',
        action='store_true',
        help='Eksportuj obrazy na każdy tick'
    )
    parser.add_argument(
        '--export_frames',
        type=int,
        nargs='*',
        default=[],
        help='Lista ticków do eksportu obrazów'
    )
    parser.add_argument(
        '-l', '--logging',
        action='store_true',
        help='Włącz logowanie na stdout'
    )

    args = parser.parse_args()

    # Wczytaj programy
    starting_population = []
    if args.input_programs:
        programs = load_programs_from_folder(args.input_programs)
        for prog in programs:
            starting_population.append({
                'program': prog['program'],
                'genome': prog['genome']
            })
        print(f"Wczytano {len(programs)} programów z {args.input_programs}")
    else:
        # Użyj domyślnego programu
        default_program = '''$PARTS:
1.0, 1.0, 1.5, 1.0, 0.5, 0.5, 1.0;

$PROGRAMM
{
    f_2(1.0, 1.0);
    IF (1.5 - X[3]) {
        f_7(1.0);
    }
    IF (X[3] - 1.5) {
        f_1(X[2], 1.0);
    }
    IF (0.0 - X[3]) {
        X[10] = X[10] + 1.0;
        IF (X[10] - 3.5) {
            X[10] = 0.0;
        }
        f_1(X[10], 1.0);
    }
    REDO;
}
'''
        starting_population.append({
            'program': default_program,
            'genome': get_default_genome()
        })
        print("Użyto domyślnego programu")

    # Uruchom symulację
    print(f"Uruchamianie symulacji: {args.time} ticków, świat {args.size[0]}x{args.size[1]}")

    df = simulate(
        resources={},
        time=args.time,
        starting_population=starting_population,
        size=args.size,
        mutation_speed=args.mutation_speed,
        mutation_type=args.mutation_type,
        visualize=args.visualize,
        seed=args.seed,
        return_data="df",
        make_timelapse=args.make_timelapse,
        export_frames=args.export_frames,
        logging_enabled=args.logging,
        output_folder=args.output_folder
    )

    # Wyświetl wyniki
    print("\n=== WYNIKI SYMULACJI ===")
    print(f"Łączna liczba automatów: {len(df)}")
    print(f"Żywych na końcu: {df['alive_at_end'].sum()}")
    print(f"Średni wiek: {df['age'].mean():.2f} ticków")
    print(f"Średnia liczba potomków: {df['offspring_count'].mean():.2f}")
    print(f"Średnia przebyta odległość: {df['total_distance_traveled'].mean():.2f}")

    # Podsumowanie zebranych zasobów
    resource_cols = [col for col in df.columns if col.endswith('_gathered')]
    if resource_cols:
        print("\n=== ZEBRANE ZASOBY ===")
        for col in resource_cols:
            total = df[col].sum()
            if total > 0:
                print(f"  {col}: {total}")

    if args.output_folder:
        print(f"\nWyniki zapisane w: {args.output_folder}")

    print("\n=== PRÓBKA DANYCH ===")
    display_cols = ['ID', 'age', 'offspring_count', 'total_distance_traveled', 'alive_at_end', 'parent_ID']
    print(df[display_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
