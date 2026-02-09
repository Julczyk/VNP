# Interpreter SRAPL

## Opis

Interpreter SRAPL (`src/srapl_interpreter.py`) wykonuje programy napisane w języku SRAPL (Self-Replicating Automata Programming Language). Wykorzystuje ANTLR4 do parsowania i implementuje wzorzec Visitor z generatorami dla krokowego wykonania.

## Architektura

```
srapl_interpreter.py
├── SRAPLExecutionVisitor   # Visitor ANTLR4 wykonujący AST
│   ├── visitProgrammSection()  # Główna pętla (obsługa RESTART)
│   ├── visitBlock()            # Blok {} (obsługa REDO)
│   ├── visitFunctionCall()     # Wywołanie f_n() -> yield
│   └── visit*Expr()            # Ewaluacja wyrażeń
│
└── SRAPLInterpreter        # Główna klasa interpretera
    ├── run_step()          # Wykonaj jeden krok symulacji
    ├── from_file()         # Wczytaj z pliku .srl
    ├── to_file()           # Zapisz do pliku .srl
    └── mutate_*()          # Placeholdery mutacji (GA)
```

## Testowanie interpretera

### 1. Test jednostkowy (standalone)

```bash
cd /home/julczyk/Dokumenty/Automaty/VNP/src
python srapl_interpreter.py
```

Uruchamia wbudowane testy z przykładowym programem. Wyświetla:
- Sparsowane skale części
- Krokowe wykonanie programu
- Stan pamięci automatu

### 2. Test z symulacją (wizualizacja)

```bash
cd /home/julczyk/Dokumenty/Automaty/VNP/src
python visual.py
```

Aby włączyć szczegółowe logi interpretera, odkomentuj w `visual.py`:
```python
setup_logging(logging.DEBUG)
```

Oraz ustaw `debug_interpreter=True`:
```python
automaton = Automaton(
    program_code=srapl_program,
    parts_genome=genome,
    world=world,
    position=(15, 15),
    debug_interpreter=True  # <- włącz debug
)
```

### 3. Test z plikiem .srl

```python
from srapl_interpreter import SRAPLInterpreter, setup_logging
import logging

# Opcjonalnie włącz debug
setup_logging(logging.DEBUG)

# Wczytaj program z pliku
interpreter = SRAPLInterpreter.from_file('examples/basic_gatherer.srl', debug=True)

# Sprawdź skale części
print(f"Parts scales: {interpreter.get_parts_specs()}")

# Mock automaton
class MockAutomaton:
    def __init__(self):
        self.memory = [0.0] * 64
        self.position = (0, 0)

mock = MockAutomaton()

# Wykonaj kilka kroków
for i in range(10):
    func_id, args = interpreter.run_step(mock)
    print(f"Step {i}: {func_id} with args {args}")
```

## Podłączanie programu do automatu

### Metoda 1: Kod inline

```python
from automaton import Automaton
from parts import Engine, Scanner, Storage, Collector, PowerGenerator

program = '''
$PARTS:
1.0, 1.0, 2.0, 1.0, 0.0, 0.0, 1.5;

$PROGRAMM
f_2(1.0, 1.0);
'''

genome = [
    (Engine, 1.0),
    (Scanner, 1.0),
    (Storage, 2.0),
    (Collector, 1.0),
    (PowerGenerator, 1.5),
]

automaton = Automaton(
    program_code=program,
    parts_genome=genome,
    world=world,
    position=(10, 10)
)
```

### Metoda 2: Z pliku .srl

```python
from srapl_interpreter import SRAPLInterpreter

# Wczytaj program
program_code = SRAPLInterpreter.load_program('examples/smart_gatherer.srl')

automaton = Automaton(
    program_code=program_code,
    parts_genome=genome,
    world=world,
    position=(10, 10)
)
```

## Logowanie i debugowanie

### Poziomy logowania

```python
from srapl_interpreter import setup_logging
import logging

# Szczegółowe logi (wszystko)
setup_logging(logging.DEBUG)

# Tylko informacje
setup_logging(logging.INFO)

# Tylko błędy
setup_logging(logging.ERROR)
```

### Przykładowy output DEBUG

```
2024-01-15 10:30:00 [SRAPL] DEBUG: Interpreter initialized, code length: 150 chars
2024-01-15 10:30:00 [SRAPL] DEBUG: [Automaton@(15, 15)] >>> Program START
2024-01-15 10:30:00 [SRAPL] DEBUG: [Automaton@(15, 15)] Assignment: X[5] = 1.0 (was 0.0)
2024-01-15 10:30:00 [SRAPL] DEBUG: [Automaton@(15, 15)] Function call: f_2([1.0, 1.0])
2024-01-15 10:30:00 [SRAPL] INFO: Step result: FunctionID.SCAN, args=[1.0, 1.0]
```

## Import/Export plików .srl

### Zapis programu

```python
from srapl_interpreter import SRAPLInterpreter

interpreter = SRAPLInterpreter(program_code)
interpreter.to_file('output/my_program.srl')

# Lub statycznie:
SRAPLInterpreter.save_program(program_code, 'output/my_program.srl')
```

### Odczyt programu

```python
# Cały interpreter z pliku
interpreter = SRAPLInterpreter.from_file('input/program.srl')

# Tylko kod (string)
code = SRAPLInterpreter.load_program('input/program.srl')
```

## Placeholdery mutacji (algorytm genetyczny)

Interpreter zawiera placeholdery dla przyszłej implementacji mutacji:

```python
interpreter = SRAPLInterpreter(program_code)

# Mutacja całego programu (zwraca nowy kod)
mutated_code = interpreter.mutate_program(mutation_rate=0.1)

# Mutacja skali części
new_scales = interpreter.mutate_parts_scales([1.0, 2.0, 1.5], mutation_rate=0.1)

# Mutacja wartości
new_value = interpreter.mutate_value(5.0, mutation_rate=0.1)

# Krzyżowanie dwóch programów
child_code = interpreter.crossover(other_interpreter)
```

**Uwaga:** Aktualnie te metody są placeholderami i zwracają dane bez zmian. Implementacja mutacji będzie rozwijana.

## Struktura pliku .srl

```
$PARTS:
<skala_0>, <skala_1>, ..., <skala_n>;

$PROGRAMM
# Komentarz
<instrukcje>
```

### Przykład

```srl
$PARTS:
1.0, 2.0, 1.5, 1.0, 0.5, 0.0, 1.0;

$PROGRAMM
# Inicjalizacja
X[0] = 100.0;

# Główna logika
IF (X[0] - 10.0) {
    f_1(0.0, 1.0);
}

f_0();
```

## Znane ograniczenia

1. Brak obsługi błędów składniowych z lokalizacją (linia/kolumna)
2. Mutacje są placeholderami (do implementacji)
3. Brak walidacji zgodności genomu z sekcją $PARTS
