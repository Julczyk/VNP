"""
Test mutacji programów SRAPL.

Testuje wszystkie typy mutacji bez uruchamiania symulacji:
1. Constant Jitter - zmiana wartości liczbowych
2. Register Mutation - zmiana indeksu X[n]
3. Node Swap - zamiana sąsiednich instrukcji
4. Add Function Call - dodanie f_n(X[k], ...)
5. Add Assignment - dodanie X[k] = expr
6. Add Control Flow - dodanie REDO/RESTART
7. Wrap With IF - opakowanie linii warunkiem IF(expr)
8. Operator Mutation - zmiana operatora matematycznego
9. Node Swell - rozbudowanie E do (E op E')
10. Delete Statement - usunięcie instrukcji

Użycie:
    python testing/genetics_tests/test_mutations.py -i program.srl -o output_folder/ -n 100
    python testing/genetics_tests/test_mutations.py -i program.srl -n 10
    python testing/genetics_tests/test_mutations.py --test-all  # Uruchom wszystkie testy
"""

import sys
import argparse
import difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from genetics import GeneticsEngine
from srapl_interpreter import SRAPLInterpreter


def generate_diff(original: str, mutated: str) -> str:
    """
    Generuje diff między oryginalnym a zmutowanym programem.
    """
    original_lines = original.splitlines(keepends=True)
    mutated_lines = mutated.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        mutated_lines,
        fromfile='0.srl (oryginal)',
        tofile='mutacja',
        lineterm=''
    )

    return ''.join(diff)


def test_mutation_types(program_code: str, num_iterations: int = 100):
    """
    Testuje różne typy mutacji i zlicza ich występowanie.
    """
    engine = GeneticsEngine(mutation_rate=0.3)  # Wyższa stawka dla lepszego testowania

    stats = {
        'total': 0,
        'changed': 0,
        'unique': set(),
        'has_new_function': 0,
        'has_new_assignment': 0,
        'has_redo': 0,
        'has_restart': 0,
        'has_if_wrap': 0,
        'has_operator_change': 0,
        'has_deleted': 0,
        'valid_syntax': 0,
    }

    for _ in range(num_iterations):
        mutated = engine.mutate_program(program_code)
        stats['total'] += 1

        if mutated != program_code:
            stats['changed'] += 1
            stats['unique'].add(mutated)

            # Sprawdź typy mutacji (heurystycznie)
            if 'f_' in mutated and mutated.count('f_') > program_code.count('f_'):
                stats['has_new_function'] += 1

            # Nowe przypisania
            if 'X[' in mutated and mutated.count('X[') > program_code.count('X['):
                stats['has_new_assignment'] += 1

            # Nowe REDO
            if mutated.count('REDO') > program_code.count('REDO'):
                stats['has_redo'] += 1

            # Nowe RESTART
            if mutated.count('RESTART') > program_code.count('RESTART'):
                stats['has_restart'] += 1

            # Nowe IF (wrap)
            if mutated.count('IF') > program_code.count('IF'):
                stats['has_if_wrap'] += 1

            # Mniej linii (delete)
            if len(mutated.strip().split('\n')) < len(program_code.strip().split('\n')):
                stats['has_deleted'] += 1

        # Test poprawności składni
        try:
            SRAPLInterpreter(mutated)
            stats['valid_syntax'] += 1
        except Exception:
            pass

    stats['unique_count'] = len(stats['unique'])
    return stats


def test_float_indices():
    """
    Testuje obsługę floatowych indeksów pamięci i funkcji.
    """
    print("\n=== Test floatowych indeksów ===")

    test_program = '''$PARTS:
1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0;

$PROGRAMM
X[2.5] = 5.0;
f_3.7(X[1.2], 2.0);
'''

    try:
        interp = SRAPLInterpreter(test_program, debug=False)
        print("  [OK] Parser zaakceptował floatowe indeksy")

        # Test wykonania
        class MockAutomaton:
            def __init__(self):
                self.memory = [0.0] * 64
                self.position = (0, 0)

        mock = MockAutomaton()
        func_id, args = interp.run_step(mock)
        print(f"  [OK] Wykonano krok: {func_id}, args={args}")

        # Sprawdź przypisanie X[2.5] -> X[2] lub X[3] (zaokrąglenie)
        if mock.memory[2] == 5.0 or mock.memory[3] == 5.0:
            print("  [OK] Przypisanie do X[2.5] działa (zaokrąglone)")
        else:
            print("  [!] Nieoczekiwana wartość pamięci")

        return True
    except Exception as e:
        print(f"  [BŁĄD] {e}")
        return False


def test_all():
    """
    Uruchamia wszystkie testy mutacji.
    """
    print("=" * 60)
    print("TESTY MUTACJI SRAPL")
    print("=" * 60)

    # Prosty program testowy
    test_program = '''$PARTS:
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
    REDO;
}
'''

    # Test 1: Generowanie mutacji
    print("\n--- Test 1: Generowanie mutacji ---")
    stats = test_mutation_types(test_program, num_iterations=50)

    print(f"  Wygenerowano: {stats['total']} mutacji")
    print(f"  Zmienionych:  {stats['changed']} ({100 * stats['changed'] / stats['total']:.1f}%)")
    print(f"  Unikalnych:   {stats['unique_count']}")
    print(f"  Poprawna składnia: {stats['valid_syntax']} ({100 * stats['valid_syntax'] / stats['total']:.1f}%)")
    print()
    print("  Typy mutacji:")
    print(f"    - Nowe funkcje:     {stats['has_new_function']}")
    print(f"    - Nowe przypisania: {stats['has_new_assignment']}")
    print(f"    - Nowe REDO:        {stats['has_redo']}")
    print(f"    - Nowe RESTART:     {stats['has_restart']}")
    print(f"    - Opakowanie IF:    {stats['has_if_wrap']}")
    print(f"    - Usunięcia:        {stats['has_deleted']}")

    # Test 2: Floatowe indeksy
    test_float_indices()

    # Test 3: Mutacja wysokiego poziomu
    print("\n--- Test 3: Mutacje wysokiego poziomu ---")
    engine = GeneticsEngine(mutation_rate=0.5)
    mutated = engine.mutate_program(test_program)

    print("  Oryginalny program:")
    for line in test_program.strip().split('\n')[:8]:
        print(f"    {line}")
    print("    ...")

    print("\n  Zmutowany program:")
    for line in mutated.strip().split('\n')[:8]:
        print(f"    {line}")
    print("    ...")

    diff = generate_diff(test_program, mutated)
    if diff:
        print("\n  Diff:")
        for line in diff.split('\n')[:15]:
            print(f"    {line}")

    print("\n" + "=" * 60)
    print("TESTY ZAKOŃCZONE")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Testowanie mutacji programów SRAPL'
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=None,
        help='Ścieżka do pliku .srl z programem'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Folder wyjściowy (0.srl = oryginał, n.srl = n-ta mutacja z diffem)'
    )
    parser.add_argument(
        '-n', '--count',
        type=int,
        default=100,
        help='Liczba mutacji do wygenerowania (domyślnie: 100)'
    )
    parser.add_argument(
        '-r', '--rate',
        type=float,
        default=0.1,
        help='Współczynnik mutacji (domyślnie: 0.1)'
    )
    parser.add_argument(
        '--test-all',
        action='store_true',
        help='Uruchom wszystkie testy bez pliku wejściowego'
    )

    args = parser.parse_args()

    if args.test_all:
        test_all()
        return

    if not args.input:
        print("Użyj --test-all lub podaj plik wejściowy -i program.srl")
        sys.exit(1)

    # Wczytaj program
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"BŁĄD: Plik {input_path} nie istnieje!")
        sys.exit(1)

    program_code = input_path.read_text(encoding='utf-8')
    print(f"Wczytano program: {input_path.name} ({len(program_code)} znaków)")

    # Inicjalizuj silnik genetyczny
    engine = GeneticsEngine(mutation_rate=args.rate)

    # Generuj mutacje
    mutations = []
    unique_mutations = set()

    print(f"Generowanie {args.count} mutacji (rate={args.rate})...")

    for i in range(args.count):
        mutated = engine.mutate_program(program_code)
        mutations.append(mutated)

        if mutated != program_code:
            unique_mutations.add(mutated)

        if (i + 1) % 10 == 0:
            print(f"  Wygenerowano {i + 1}/{args.count} mutacji...")

    # Statystyki
    changed_count = sum(1 for m in mutations if m != program_code)
    unique_count = len(unique_mutations)

    # Test składni
    valid_count = 0
    for m in mutations:
        try:
            SRAPLInterpreter(m)
            valid_count += 1
        except Exception:
            pass

    print()
    print("=" * 60)
    print(f"WYNIKI:")
    print(f"  Wygenerowano mutacji:     {args.count}")
    print(f"  Zmienionych programów:    {changed_count} ({100 * changed_count / args.count:.1f}%)")
    print(f"  Unikalnych mutacji:       {unique_count}")
    print(f"  Poprawna składnia:        {valid_count} ({100 * valid_count / args.count:.1f}%)")
    print("=" * 60)

    # Zapis wyników
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Zapisz oryginał jako 0.srl
        original_file = output_dir / "0.srl"
        original_file.write_text(program_code, encoding='utf-8')
        print(f"Zapisano oryginał: {original_file}")

        # Zapisz mutacje jako n.srl
        saved_count = 0
        for i, mutated in enumerate(mutations, start=1):
            mutation_file = output_dir / f"{i}.srl"

            # Generuj diff
            diff = generate_diff(program_code, mutated)

            # Zawartość pliku: program + diff jako komentarz
            content = mutated
            if diff:
                content += "\n\n# === DIFF vs ORYGINAŁ ===\n"
                for line in diff.splitlines():
                    content += f"# {line}\n"

            mutation_file.write_text(content, encoding='utf-8')
            saved_count += 1

        print(f"Zapisano {saved_count} mutacji do: {output_dir}")

    else:
        print()
        print("PRZYKŁADOWE MUTACJE (pierwsze 5 unikalnych):")
        print("-" * 60)
        shown = 0
        for i, mutated in enumerate(mutations):
            if mutated != program_code and shown < 5:
                print(f"\n--- Mutacja {i + 1} ---")
                print(mutated)
                print("\n--- DIFF ---")
                print(generate_diff(program_code, mutated))
                shown += 1


if __name__ == "__main__":
    main()
