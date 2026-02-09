# Struktura projektu VNP

```
VNP/
├── CLAUDE.md                 # Instrukcje dla Claude Code
├── README.md                 # Opis projektu
├── SRAPL.g4                  # Gramatyka ANTLR4 języka SRAPL
│
├── src/                      # Kod źródłowy
│   ├── config.py             # Konfiguracja, enumy, mapowania f_n -> Part
│   ├── automaton.py          # Klasa Automaton - główna jednostka symulacji
│   ├── parts.py              # Klasy części (Engine, Scanner, Storage, etc.)
│   ├── stats.py              # System statystyk automatów
│   ├── srapl_interpreter.py  # Główny interpreter SRAPL (ANTLR4)
│   ├── visual.py             # Wizualizacja (Arcade)
│   │
│   ├── world/                # Świat symulacji
│   │   ├── world.py          # Klasa World - mapa, zasoby, automaty
│   │   └── tile.py           # Klasy Tile, WaterTile
│   │
│   ├── sraplBase/            # Pliki wygenerowane przez ANTLR4
│   │   ├── SRAPLLexer.py
│   │   ├── SRAPLParser.py
│   │   └── SRAPLVisitor.py
│   │
│   ├── interpreter.py        # Stary prosty interpreter (deprecated)
│   ├── genetics.py           # Mutacje (placeholder)
│   ├── Main.py               # Pusty entry point
│   └── Simulation.py         # Pusty koordynator
│
├── docs/                     # Dokumentacja
│   ├── jezyk.md              # Specyfikacja języka SRAPL
│   ├── parts.md              # Opis części i ich funkcji
│   ├── opis.md               # Cele projektu
│   ├── interpreter.md        # Użycie interpretera
│   ├── stats.md              # System statystyk
│   └── struktura.md          # Ten plik
│
├── examples/                 # Przykładowe programy SRAPL
│   ├── basic_gatherer.srl
│   └── smart_gatherer.srl
│
├── testing/                  # Testy
│   ├── test_stats.py         # Test systemu statystyk
│   │
│   ├── interpreter_tests/    # Testy interpretera SRAPL
│   │   ├── run_all_tests.py
│   │   ├── test_basic_scan.py
│   │   ├── test_if_conditions.py
│   │   ├── test_redo_restart.py
│   │   ├── test_nested_blocks.py
│   │   ├── test_file_loading.py
│   │   ├── test_multiple_automata.py
│   │   └── test_expressions.py
│   │
│   ├── basic_sim/            # Testy podstawowej symulacji
│   │   ├── test_survivor.py
│   │   ├── test_gatherer.py
│   │   ├── test_reproducer.py
│   │   ├── test_lifecycle.py
│   │   └── test_ecosystem.py
│   │
│   └── program_tests/        # Testy programów z plików
│       ├── run_multi_program_sim.py
│       └── start_programs/   # Programy .srl do wczytania
│           ├── gatherer.srl
│           ├── lazy.srl
│           └── explorer.srl
│
└── prompting/                # Prompty dla AI (wewnętrzne)
```

## Mapowanie funkcji f_n na części

| f_n | FunctionID | Klasa części | Opis |
|-----|------------|--------------|------|
| f_0 | IDLE | PowerGenerator | Odpoczynek, produkcja energii |
| f_1 | MOVE | Engine | Ruch |
| f_2 | SCAN | Scanner | Skanowanie otoczenia |
| f_3 | STORE | Storage | Zarządzanie magazynem |
| f_4 | SMELT | Smelter | Przetwarzanie rudy |
| f_5 | ASSEMBLE | Assembler | Produkcja części |
| f_7 | COLLECT | Collector | Zbieranie zasobów |

## Kolejność części w $PARTS

```
$PARTS:
<Engine>,      # indeks 0
<Scanner>,     # indeks 1
<Storage>,     # indeks 2
<Collector>,   # indeks 3
<Smelter>,     # indeks 4
<Assembler>,   # indeks 5
<PowerGenerator>; # indeks 6
```

## Przepływ danych

```
SRAPL (.srl)
    ↓
SRAPLInterpreter (ANTLR4 parser + visitor)
    ↓
Automaton.update()
    ↓ func_id, args
part_map[func_id].execute_action(automaton, args)
    ↓
World.update() → visual.py (Arcade)
```
