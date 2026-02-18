# Algorytm genetyczny

## Przegląd

System genetyczny VNP umożliwia ewolucję programów SRAPL poprzez mutacje na poziomie AST (Abstract Syntax Tree). Mutacje są stosowane podczas reprodukcji automatu.

## Implementacja

Silnik genetyczny znajduje się w `src/genetics.py` i składa się z:

### GeneticsEngine

Główna klasa odpowiedzialna za mutacje programów SRAPL.

```python
from genetics import GeneticsEngine

engine = GeneticsEngine(mutation_rate=0.1)
mutated_code = engine.mutate_program(original_code)
```

**Parametry:**
- `mutation_rate` (float, 0.0-1.0): prawdopodobieństwo mutacji każdego węzła AST

### SRAPLCodeGenerator

Visitor konwertujący drzewo AST z powrotem do kodu SRAPL. Obsługuje atrybuty mutacji dodane przez GeneticsEngine.

## Typy mutacji

### Mutacje sekcji $PARTS

Wartości w sekcji `$PARTS` podlegają mutacji - zmiana o losową wartość z zakresu ±0.3.
Wartość nie może spaść poniżej 0 - jeśli wynik byłby ujemny, mutacja jest odrzucana.

**Parametry:**
- `PARTS_JITTER_RANGE = 0.3`

**Przykład:**
```
Przed: $PARTS: 1.0, 1.2, 0.8;
Po:    $PARTS: 1.1, 1.0, 0.9;
```

### Mutacje sekcji $PROGRAMM

### 1. Constant Jitter (Mutacja stałych)
Zmienia wartości liczbowe w wyrażeniach o losową wartość z zakresu ±0.5.

**Przykład:**
```
Przed: X[5] = 10.0;
Po:    X[5] = 10.3;
```

**Parametry:**
- `CONSTANT_JITTER_RANGE = 0.5`

### 2. Register Mutation (Mutacja rejestrów)
Zmienia indeksy pamięci X[n] o losową wartość z zakresu ±2.

**Przykład:**
```
Przed: IF (X[3] - 1.5) { ... }
Po:    IF (X[5] - 1.5) { ... }
```

**Parametry:**
- `REGISTER_MUTATION_RANGE = 2`
- `MEMORY_INDEX_MAX = 63`

### 3. Statement Swap (Zamiana instrukcji)
Zamienia miejscami dwie sąsiednie instrukcje w bloku kodu.

**Przykład:**
```
Przed:                    Po:
f_2(1.0, 1.0);           IF (1.5 - X[3]) {
IF (1.5 - X[3]) {            f_7(1.0);
    f_7(1.0);            }
}                        f_2(1.0, 1.0);
```

### 4. Add Function Call (Dodanie wywołania funkcji)
Dodaje losowe wywołanie funkcji robota (f_0 do f_8) z losowymi argumentami.

**Przykład:**
```
Przed:              Po:
f_2(1.0);          f_2(1.0);
REDO;              f_5(X[12], 2.3);
                   REDO;
```

### 5. Add Assignment (Dodanie przypisania)
Dodaje losowe przypisanie do pamięci.

**Przykład:**
```
Przed:              Po:
f_2(1.0);          f_2(1.0);
                   X[15] = (3.2 + X[4]);
```

### 6. Add Control Flow (Dodanie sterowania)
Dodaje instrukcję REDO lub RESTART.

**Przykład:**
```
Przed:              Po:
f_7(1.0);          f_7(1.0);
                   REDO;
```

### 7. Wrap With IF (Opakowanie w IF)
Opakowuje istniejącą instrukcję w blok IF z losowym warunkiem.

**Przykład:**
```
Przed:                      Po:
f_7(1.0);                  IF (X[8] - 2.1) {
                               f_7(1.0);
                           }
```

### 8. Operator Mutation (Zmiana operatora)
Zamienia operator matematyczny (+, -, *, /) na inny.

**Przykład:**
```
Przed: X[5] = X[3] + 1.0;
Po:    X[5] = X[3] * 1.0;
```

### 9. Node Swell (Rozbudowa węzła)
Rozbudowuje proste wyrażenie E do (E op E'), gdzie E' to losowy atom.

**Przykład:**
```
Przed: X[5] = 3.0;
Po:    X[5] = (3.0 + X[12]);
```

### 10. Delete Statement (Usunięcie instrukcji)
Usuwa losową instrukcję z bloku (nie usuwa ostatniej instrukcji w bloku).

## Integracja z reprodukcją

W metodzie `Automaton.reproduce()` (`src/automaton.py`):

```python
# Mutacja programu
genetics = GeneticsEngine(mutation_rate=0.1)
mutated_program = genetics.mutate_program(self.interpreter.program)

# Mutacja genomu części (skala ±10%)
mutated_genome = []
for part_cls, scale in self.parts_genome:
    if random.random() < 0.1:
        mutation_factor = random.uniform(0.9, 1.1)
        new_scale = max(0.1, scale * mutation_factor)
        mutated_genome.append((part_cls, new_scale))
    else:
        mutated_genome.append((part_cls, scale))

# Tworzenie dziecka z mutacjami (z parent_id dla lineage tracking)
child = Automaton(
    program_code=mutated_program,
    parts_genome=mutated_genome,
    parent_id=self.stats.automaton_id,
    ...
)
```

## Walidacja

GeneticsEngine automatycznie waliduje wygenerowany kod:
1. Parsuje zmutowany kod przy użyciu ANTLR4
2. Jeśli parsing się nie powiedzie, próbuje ponownie (do 5 razy)
3. Jeśli wszystkie próby zawiodą, zwraca oryginalny kod

## Klasa Mutator (kompatybilność wsteczna)

Dla kompatybilności wstecznej dostępna jest klasa `Mutator`:

```python
from genetics import Mutator

# Mutacja genomu
mutated_genome = Mutator.mutate_genome(parts_genome, mutation_rate=0.1)

# Mutacja programu
mutated_code = Mutator.mutate_program(program_code, mutation_rate=0.1)
```

## Testowanie

```bash
cd src
python -c "
from genetics import GeneticsEngine

code = '''
\$PARTS:
1.0, 1.0, 2.0, 1.0, 0.5, 0.5, 1.5;

\$PROGRAMM
{
    f_2(1.0, 1.0);
    IF (1.5 - X[3]) {
        f_7(1.0);
    }
    REDO;
}
'''

engine = GeneticsEngine(mutation_rate=0.2)
mutated = engine.mutate_program(code)
print(mutated)
"
```

## System eksperymentów ewolucyjnych

Wieloetapowe eksperymenty ewolucji w `testing/final/evolution.ipynb`.

### Architektura eksperymentu

Eksperyment składa się z wielu **etapów (generacji)**. W każdym etapie:

1. **Symulacja etapu**: Uruchamiana z parametrami z notebooka
2. **Analiza statystyk**: Obliczane są średnie, sumy dla różnych metryk
3. **Selekcja**: Wybierana jest grupa najlepszych automatów do następnego etapu
4. **Ewaluacja równoległa**: Dla wybranych automatów uruchamiane są krótkie symulacje ewaluacyjne
5. **Zapis wyników**: Programy, statystyki i klatki zapisywane do folderu results/

### Parametry eksperymentu

```python
STAGES = 5              # Liczba etapów (generacji)
TO_NEXT = 5             # Automaty przechodące do następnego etapu
EVAL_COUNT = 3          # Automaty do ewaluacji (eval < to_next)

# Parametry symulacji etapu
STAGE_PARAMS = {
    'time': 500,        # Czas trwania (ticki)
    'size': [80, 80],   # Rozmiar świata
    'mutation_speed': 0.1,
    'mutation_type': 'all',
    # ...
}

# Parametry ewaluacji (bez mutacji)
EVAL_PARAMS = {
    'time': 100,        # Krótki czas
    'mutation_speed': 0,
    'mutation_type': 'disabled',
    # ...
}
```

### Selekcja

Fitness automatu obliczany jako:
```python
fitness = offspring_count * 10 + age * 0.5 + total_resources * 2
```

### Struktura wyników

```
results/evolution_YYYYMMDD_HHMMSS/
├── generation_0/
│   ├── stage_results.csv      # DataFrame z etapu
│   ├── stage_stats.json       # Statystyki podsumowujące
│   ├── programs/              # Programy przetrwałych
│   │   ├── 1.srl
│   │   └── 2.srl
│   └── evals/                 # Wyniki ewaluacji
│       ├── 1.json
│       └── 2.json
├── generation_1/
│   └── ...
├── competitions/              # Symulacje rywalizacji
│   └── comp_HHMMSS/
│       ├── frames/
│       └── competition.mp4
├── experiment_summary.png     # Wykresy podsumowujące
├── population_history.png     # Historia populacji w czasie
└── summary.txt               # Podsumowanie tekstowe
```

### Funkcje pomocnicze

```python
# Ewaluacja pojedynczego automatu
df = evaluate_automaton(automaton_id=1, generation=0, time=200)

# Rywalizacja między automatami na dużej mapie
df = run_competition([
    {'id': 1, 'generation': 0},
    {'id': 2, 'generation': 1}
], map_size=120, make_video=True)
```

### Uruchomienie

```bash
cd testing/final
jupyter notebook evolution.ipynb
# lub
jupyter lab evolution.ipynb
```

### Wykresy generowane automatycznie

1. **Populacja w etapach** - słupki łącznej liczby i żywych na końcu
2. **Średni wiek** - trend w kolejnych etapach
3. **Średnia potomków** - trend reprodukcji
4. **Zebrane zasoby** - sumy dla różnych typów zasobów
5. **Energia** - średnia wyprodukowana vs zużyta
6. **Ewaluacja** - mediana zebranych zasobów per etap
