#!/usr/bin/env python3
"""
Uruchamia wszystkie testy interpretera po kolei.
Po zamknięciu okna każdego testu, uruchomi się następny.

Użycie:
    python testing/interpreter_tests/run_all_tests.py

Opcje:
    --no-visual    Uruchom tylko testy bez wizualizacji (sprawdź importy i parsowanie)
    --test N       Uruchom tylko test numer N (1-7)
"""

import sys
import subprocess
from pathlib import Path

# Ścieżka do katalogu testów
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent.parent

TESTS = [
    ("test_basic_scan.py", "Podstawowe skanowanie"),
    ("test_if_conditions.py", "Instrukcje warunkowe IF"),
    ("test_redo_restart.py", "REDO i RESTART"),
    ("test_nested_blocks.py", "Zagnieżdżone bloki"),
    ("test_file_loading.py", "Wczytywanie z pliku .srl"),
    ("test_multiple_automata.py", "Wiele automatów"),
    ("test_expressions.py", "Wyrażenia matematyczne"),
]


def run_visual_test(test_file: str, description: str):
    """Uruchamia test wizualny."""
    print("\n" + "=" * 60)
    print(f"TEST: {description}")
    print(f"Plik: {test_file}")
    print("=" * 60)
    print("Zamknij okno wizualizacji, aby przejść do następnego testu.\n")

    result = subprocess.run(
        [sys.executable, str(TEST_DIR / test_file)],
        cwd=str(PROJECT_ROOT)
    )

    return result.returncode == 0


def run_import_test(test_file: str, description: str):
    """Testuje tylko import i parsowanie (bez wizualizacji)."""
    print(f"\n[{description}] ", end="")

    # Kod testujący import i parsowanie
    test_code = f'''
import sys
sys.path.insert(0, "{PROJECT_ROOT / 'src'}")

# Importy
from srapl_interpreter import SRAPLInterpreter
from automaton import Automaton
from world.world import World
from parts import Engine, Scanner, Storage, Collector, PowerGenerator

# Test parsowania z pliku testu
test_file = "{TEST_DIR / test_file}"
with open(test_file, "r") as f:
    content = f.read()

# Znajdź program SRAPL w pliku testu
import re
match = re.search(r"PROGRAM.*?=\\s*[\\'\\"]{3}(.*?)[\\'\\"]{3}", content, re.DOTALL)
if match:
    program = match.group(1)
    # Test parsowania
    try:
        interp = SRAPLInterpreter(program)
        scales = interp.get_parts_specs()
        print(f"OK - scales: {{scales}}")
    except Exception as e:
        print(f"BŁĄD parsowania: {{e}}")
        sys.exit(1)
else:
    print("POMINIĘTO - nie znaleziono programu SRAPL")
'''

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )

    print(result.stdout.strip())
    if result.stderr:
        print(f"  Błędy: {result.stderr.strip()}")

    return result.returncode == 0


def main():
    args = sys.argv[1:]

    # Parsowanie argumentów
    no_visual = "--no-visual" in args

    test_num = None
    for i, arg in enumerate(args):
        if arg == "--test" and i + 1 < len(args):
            try:
                test_num = int(args[i + 1])
            except ValueError:
                pass

    print("=" * 60)
    print("TESTY INTERPRETERA SRAPL")
    print("=" * 60)

    if no_visual:
        print("Tryb: tylko importy i parsowanie (bez wizualizacji)\n")
    else:
        print("Tryb: pełne testy wizualne")
        print("Zamykaj kolejne okna, aby przechodzić między testami.\n")

    # Wybór testów do uruchomienia
    if test_num is not None:
        if 1 <= test_num <= len(TESTS):
            tests_to_run = [TESTS[test_num - 1]]
        else:
            print(f"Błąd: test {test_num} nie istnieje (dostępne: 1-{len(TESTS)})")
            sys.exit(1)
    else:
        tests_to_run = TESTS

    # Uruchomienie testów
    passed = 0
    failed = 0

    for test_file, description in tests_to_run:
        if no_visual:
            success = run_import_test(test_file, description)
        else:
            success = run_visual_test(test_file, description)

        if success:
            passed += 1
        else:
            failed += 1

    # Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    print(f"Zaliczone: {passed}")
    print(f"Niezaliczone: {failed}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
