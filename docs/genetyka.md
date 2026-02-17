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

### 1. Constant Jitter (Mutacja stałych)
Zmienia wartości liczbowe o losową wartość z zakresu ±0.5.

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

## Gold Fitness Evolution

System ewolucji wykorzystujący gold_fitness jako kryterium selekcji.

### Koncepcja

Gold fitness = suma złota zebranego przez automata + wszystkich jego potomków.

Ta miara faworyzuje automaty, które:
1. Zbierają złoto efektywnie
2. Reprodukują się (przekazują geny)
3. Mają potomstwo, które również zbiera złoto

### Uruchomienie ewolucji

```bash
python testing/genetics_tests_gold/run_gold_evolution.py \
  -i testing/genetics_tests_gold/start.srl \
  -k 10 \   # 10 iteracji
  -t 1000 \ # 1000 ticków per iteracja
  -n 5      # 5 automatów w populacji
```

### Algorytm

1. **Inicjalizacja**: n kopii programu startowego
2. **Symulacja**: Uruchom symulację przez t ticków
3. **Ewaluacja**: Oblicz gold_fitness dla każdego startowego automatu
4. **Selekcja**: Wybierz n najlepszych programów
5. **Mutacja**: Zastosuj mutacje do wybranych programów
6. **Powtórz**: Wróć do kroku 2 (k iteracji)

### Parametry konfiguracyjne

W `src/config.py`:

```python
GOLD_FITNESS_TIME = 200      # Po ilu tickach raportować gold_fitness
RANDOM_DEATH_CHANCE = 0.01   # Szansa na losową śmierć (1% per tick)
```

### Wyniki

Skrypt zapisuje:
- `evolution_history.json` - pełna historia wszystkich iteracji
- `final_report.csv` - podsumowanie (avg/max/min gold_fitness per iteracja)
- `best_programs/` - najlepsze programy z ostatniej iteracji

### Przykładowe wyjście CSV

```csv
iteration,avg_gold_fitness,max_gold_fitness,min_gold_fitness,total_automata
1,2.40,5,0,47
2,3.80,8,1,52
3,5.20,12,2,61
...
```
