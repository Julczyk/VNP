#!/usr/bin/env python3
"""
Test skryptu Simulation.py.

Uruchamia symulację z przykładowymi programami i weryfikuje wyniki.

Użycie:
    python testing/final_test/run_test.py
    python testing/final_test/run_test.py --visualize
    python testing/final_test/run_test.py --time 500 --output results/
"""

import sys
import argparse
from pathlib import Path

# Dodaj ścieżkę src do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from Simulation import simulate, load_programs_from_folder, get_default_genome


def run_basic_test():
    """Test podstawowy - krótka symulacja bez wizualizacji."""
    print("=== TEST PODSTAWOWY ===")

    input_folder = Path(__file__).parent / "input_programs"
    programs = load_programs_from_folder(str(input_folder))

    print(f"Wczytano {len(programs)} programów")

    starting_population = [
        {'program': p['program'], 'genome': p['genome']}
        for p in programs
    ]

    df = simulate(
        time=100,
        starting_population=starting_population,
        size=[40, 40],
        mutation_speed=0.1,
        mutation_type="all",
        visualize=False,
        seed=42,
        return_data="df",
        logging_enabled=True
    )

    print(f"\n=== WYNIKI TESTU ===")
    print(f"Łączna liczba automatów: {len(df)}")
    print(f"Żywych na końcu: {df['alive_at_end'].sum()}")

    # Walidacja
    assert len(df) >= len(starting_population), "Powinno być co najmniej tyle automatów co startowych"
    assert 'ID' in df.columns, "Brak kolumny ID"
    assert 'age' in df.columns, "Brak kolumny age"
    assert 'offspring_count' in df.columns, "Brak kolumny offspring_count"
    assert 'parent_ID' in df.columns, "Brak kolumny parent_ID"

    print("\n[OK] Test podstawowy zakończony pomyślnie!")
    return df


def run_mutation_test():
    """Test mutacji - sprawdza czy mutacje działają."""
    print("\n=== TEST MUTACJI ===")

    default_program = '''$PARTS:
1.0, 1.0, 1.5, 1.0, 0.5, 0.5, 1.0;

$PROGRAMM
{
    f_2(1.0, 1.0);
    IF (1.5 - X[3]) {
        f_7(1.0);
    }
    f_1(X[2], 1.0);
    REDO;
}
'''

    # Test z wyłączonymi mutacjami
    df_no_mut = simulate(
        time=50,
        starting_population=[{'program': default_program, 'genome': get_default_genome()}],
        size=[30, 30],
        mutation_speed=0,
        mutation_type="disabled",
        visualize=False,
        seed=42,
        logging_enabled=False
    )

    # Test z włączonymi mutacjami
    df_with_mut = simulate(
        time=50,
        starting_population=[{'program': default_program, 'genome': get_default_genome()}],
        size=[30, 30],
        mutation_speed=0.3,
        mutation_type="all",
        visualize=False,
        seed=42,
        logging_enabled=False
    )

    print(f"Bez mutacji: {len(df_no_mut)} automatów")
    print(f"Z mutacjami: {len(df_with_mut)} automatów")

    print("\n[OK] Test mutacji zakończony!")
    return df_no_mut, df_with_mut


def run_output_test(output_folder: str):
    """Test zapisu wyników do folderu."""
    print("\n=== TEST ZAPISU WYNIKÓW ===")

    input_folder = Path(__file__).parent / "input_programs"
    programs = load_programs_from_folder(str(input_folder))

    starting_population = [
        {'program': p['program'], 'genome': p['genome']}
        for p in programs[:2]  # Użyj tylko 2 programów
    ]

    df = simulate(
        time=50,
        starting_population=starting_population,
        size=[30, 30],
        mutation_speed=0.1,
        visualize=False,
        seed=42,
        output_folder=output_folder,
        logging_enabled=False
    )

    output_path = Path(output_folder)
    assert (output_path / "results.csv").exists(), "Brak pliku results.csv"
    assert (output_path / "report.txt").exists(), "Brak pliku report.txt"

    print(f"Wyniki zapisane w: {output_folder}")
    print("\n[OK] Test zapisu zakończony!")
    return df


def main():
    parser = argparse.ArgumentParser(description='Testy Simulation.py')
    parser.add_argument('-v', '--visualize', action='store_true', help='Pokaż wizualizację')
    parser.add_argument('-t', '--time', type=int, default=100, help='Czas symulacji')
    parser.add_argument('-o', '--output', type=str, default=None, help='Folder wyjściowy')

    args = parser.parse_args()

    print("=" * 60)
    print("TESTY SIMULATION.PY")
    print("=" * 60)

    # Test podstawowy
    df = run_basic_test()

    # Test mutacji
    run_mutation_test()

    # Test zapisu (jeśli podano folder)
    if args.output:
        run_output_test(args.output)

    # Test z wizualizacją (opcjonalny)
    if args.visualize:
        print("\n=== TEST Z WIZUALIZACJĄ ===")
        input_folder = Path(__file__).parent / "input_programs"
        programs = load_programs_from_folder(str(input_folder))

        starting_population = [
            {'program': p['program'], 'genome': p['genome']}
            for p in programs
        ]

        simulate(
            time=args.time,
            starting_population=starting_population,
            size=[60, 60],
            mutation_speed=0.1,
            visualize=True,
            seed=42,
            logging_enabled=True
        )

    print("\n" + "=" * 60)
    print("WSZYSTKIE TESTY ZAKOŃCZONE POMYŚLNIE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
