"""
Test 1: Generowanie mutacji programów SRAPL.

Wczytuje program z pliku .srl, generuje N mutacji i wypisuje wyniki.

Użycie:
    python testing/genetics_tests/test_mutations.py -i program.srl -o output_folder/ -n 100
    python testing/genetics_tests/test_mutations.py -i program.srl -n 10
"""

import sys
import argparse
import difflib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from genetics import GeneticsEngine


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


def main():
    parser = argparse.ArgumentParser(
        description='Generowanie mutacji programów SRAPL'
    )
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
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

    args = parser.parse_args()

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

    print()
    print("=" * 60)
    print(f"WYNIKI:")
    print(f"  Wygenerowano mutacji:     {args.count}")
    print(f"  Zmienionych programów:    {changed_count} ({100 * changed_count / args.count:.1f}%)")
    print(f"  Unikalnych mutacji:       {unique_count}")
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
