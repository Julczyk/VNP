# Implementacja interpretera języka SRAPL

## Decyzje architektoniczne

### Visitor vs Listener

Wybrałem podejście **bez użycia wygenerowanego Visitora/Listenera** z ANTLR, a zamiast tego bezpośrednie chodzenie po drzewie AST. Powody:

1. **Kontrola przepływu z generatorami** - Kluczowym wymaganiem jest wznowienie programu po wywołaniu `f_n`. Generatory Pythona (`yield`) naturalnie to wspierają, ale źle się komponują z tradycyjnym Visitorem.

2. **Obsługa REDO/RESTART** - Te instrukcje wymagają skoków, które łatwiej zaimplementować z własną logiką niż przez Visitor pattern.

3. **Prostota debugowania** - Bezpośredni kod jest łatwiejszy do śledzenia niż callback'i Visitora.

Gdybym używał czystego Visitora, musiałbym:
- Przekształcić AST na bytecode/listę instrukcji
- Lub używać skomplikowanego stosu kontynuacji

### Mechanizm wznowienia

Używam **generatorów Pythona** - każda instrukcja, która może zawierać wywołanie funkcji, jest generatorem. Gdy napotykamy `f_n()`, `yield`ujemy wynik i wstrzymujemy wykonanie. Przy następnym wywołaniu `run_step()` generator kontynuuje od tego miejsca.

---

## Implementacja

### Plik: `srapl_interpreter.py`

```python
"""
Interpreter języka SRAPL (Self-Replicating Automaton Programming Language)

Używa generatorów Pythona do realizacji wznowienia programu
po wywołaniu funkcji f_n.
"""

from antlr4 import CommonTokenStream, InputStream
from SRAPLLexer import SRAPLLexer
from SRAPLParser import SRAPLParser


class RedoException(Exception):
    """Sygnał do powtórzenia bieżącego bloku"""
    pass


class RestartException(Exception):
    """Sygnał do restartu całego programu"""
    pass


class SRAPLInterpreter:
    """
    Główny interpreter języka SRAPL.
    
    Cechy:
    - Parsuje kod źródłowy przy inicjalizacji
    - Wykonuje program krok po kroku (każdy krok kończy się wywołaniem f_n)
    - Obsługuje wznowienie wykonania po wywołaniu funkcji
    - Obsługuje REDO (powtórzenie bloku) i RESTART (restart programu)
    """
    
    def __init__(self, program_code: str, memory_size: int = 64):
        """
        Args:
            program_code: Kod źródłowy programu SRAPL
            memory_size: Rozmiar pamięci automatu (tablica floatów)
        """
        self.program_code = program_code
        self.memory = [0.0] * memory_size
        self.parts_scales = []
        
        self._parse_program()
        self._execution_generator = None
        self._max_iterations = 10000  # Zabezpieczenie przed nieskończoną pętlą
    
    def _parse_program(self):
        """Parsuje kod źródłowy i wyciąga AST oraz skale części"""
        input_stream = InputStream(self.program_code)
        lexer = SRAPLLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = SRAPLParser(token_stream)
        
        # Sprawdzenie błędów parsowania
        parser.removeErrorListeners()
        error_listener = SRAPLErrorListener()
        parser.addErrorListener(error_listener)
        
        self.tree = parser.file_()
        
        if error_listener.errors:
            raise SyntaxError(f"Błędy parsowania: {error_listener.errors}")
        
        # Wyciągamy skale części z sekcji $PARTS
        parts_section = self.tree.partsSection()
        if parts_section and parts_section.floatList():
            for val in parts_section.floatList().value():
                if val.FLOAT():
                    self.parts_scales.append(float(val.FLOAT().getText()))
                else:
                    self.parts_scales.append(float(val.INT().getText()))
        
        self.program_section = self.tree.programmSection()
    
    def get_parts_scales(self) -> list:
        """Zwraca listę skal części z sekcji $PARTS"""
        return self.parts_scales.copy()
    
    def run_step(self, robot=None) -> tuple:
        """
        Wykonuje jeden krok programu.
        
        Program wykonuje się aż do napotkania wywołania funkcji f_n,
        które kończy krok i zwraca kontrolę do symulacji.
        
        Args:
            robot: Opcjonalny obiekt automatu (do synchronizacji pamięci)
        
        Returns:
            Tuple (func_id: int, args: list[float]) - ID funkcji i argumenty
        """
        if robot is not None:
            self.memory = robot.memory
        
        if self._execution_generator is None:
            self._execution_generator = self._main_loop()
        
        try:
            result = next(self._execution_generator)
            if robot is not None:
                robot.memory = self.memory
            return result
        except StopIteration:
            # Program się zakończył - restart
            self._execution_generator = self._main_loop()
            return self.run_step(robot)
        except RestartException:
            self._execution_generator = self._main_loop()
            return self.run_step(robot)
    
    def _main_loop(self):
        """
        Główna pętla programu (generator).
        
        Program stanowi nieskończoną pętlę - po dojściu do końca
        zaczyna się od nowa.
        """
        iterations = 0
        while True:
            try:
                yield from self._execute_block_content(
                    self.program_section.blockContent()
                )
                # Po zakończeniu programu - restart od początku
                iterations += 1
                if iterations > self._max_iterations:
                    # Zabezpieczenie - program nie wywołał żadnej funkcji
                    yield (0, [])  # Domyślnie IDLE
                    iterations = 0
            except RestartException:
                iterations = 0
                continue
    
    def _execute_block_content(self, ctx):
        """Wykonuje zawartość bloku (sekwencję instrukcji)"""
        if ctx is None:
            return
        
        statements = ctx.statement() if ctx.statement() else []
        for stmt in statements:
            yield from self._execute_statement(stmt)
    
    def _execute_statement(self, stmt):
        """Wykonuje pojedynczą instrukcję"""
        if stmt.assignment():
            self._execute_assignment(stmt.assignment())
        elif stmt.functionCall():
            result = self._execute_function_call(stmt.functionCall())
            yield result  # Zwraca (func_id, args) i wstrzymuje wykonanie
        elif stmt.ifStatement():
            yield from self._execute_if(stmt.ifStatement())
        elif stmt.redoStatement():
            raise RedoException()
        elif stmt.restartStatement():
            raise RestartException()
        elif stmt.block():
            yield from self._execute_block(stmt.block())
    
    def _execute_block(self, ctx):
        """
        Wykonuje blok kodu z obsługą REDO.
        
        REDO powoduje powtórzenie całego bloku od początku.
        """
        max_redo = 1000  # Zabezpieczenie
        redo_count = 0
        
        while redo_count < max_redo:
            try:
                yield from self._execute_block_content(ctx.blockContent())
                break  # Normalnie kończymy blok
            except RedoException:
                redo_count += 1
                continue  # REDO - powtarzamy blok
        
        if redo_count >= max_redo:
            # Zbyt wiele powtórzeń - przerywamy
            yield (0, [])
    
    def _execute_assignment(self, ctx):
        """Wykonuje przypisanie X[i] = expr"""
        mem_ref = ctx.memoryRef()
        index = int(mem_ref.INT().getText())
        value = self._evaluate_expression(ctx.expression())
        
        if 0 <= index < len(self.memory):
            self.memory[index] = float(value)
    
    def _execute_function_call(self, ctx) -> tuple:
        """
        Parsuje wywołanie funkcji i zwraca krotkę (func_id, args).
        
        Funkcje mają postać f_N gdzie N to numer.
        """
        func_text = ctx.FUNC_ID().getText()
        func_id = int(func_text[2:])  # Wyciągamy numer z "f_N"
        
        args = []
        if ctx.argList():
            for expr in ctx.argList().expression():
                args.append(float(self._evaluate_expression(expr)))
        
        return (func_id, args)
    
    def _execute_if(self, ctx):
        """
        Wykonuje instrukcję IF.
        
        Blok wykonuje się gdy wyrażenie warunku > 0.
        """
        condition = self._evaluate_expression(ctx.expression())
        if condition > 0:
            yield from self._execute_block(ctx.block())
    
    def _evaluate_expression(self, ctx) -> float:
        """
        Oblicza wartość wyrażenia matematycznego.
        
        Obsługuje:
        - Operatory: +, -, *, /, **
        - Nawiasy
        - Odwołania do pamięci: X[i]
        - Literały liczbowe (int i float)
        """
        if ctx is None:
            return 0.0
        
        # Pobierz nazwę klasy kontekstu (określa typ wyrażenia)
        class_name = type(ctx).__name__
        
        if class_name == 'ParensExprContext':
            # Wyrażenie w nawiasach: (expr)
            return self._evaluate_expression(ctx.expression())
        
        elif class_name == 'PowerExprContext':
            # Potęgowanie: expr ** expr
            left = self._evaluate_expression(ctx.expression(0))
            right = self._evaluate_expression(ctx.expression(1))
            try:
                return float(left ** right)
            except (ValueError, OverflowError):
                return 0.0
        
        elif class_name == 'MulDivExprContext':
            # Mnożenie/dzielenie: expr * expr lub expr / expr
            left = self._evaluate_expression(ctx.expression(0))
            right = self._evaluate_expression(ctx.expression(1))
            if ctx.MUL():
                return left * right
            else:  # DIV
                if right == 0:
                    return 0.0  # Dzielenie przez zero
                return left / right
        
        elif class_name == 'AddSubExprContext':
            # Dodawanie/odejmowanie: expr + expr lub expr - expr
            left = self._evaluate_expression(ctx.expression(0))
            right = self._evaluate_expression(ctx.expression(1))
            if ctx.PLUS():
                return left + right
            else:  # MINUS
                return left - right
        
        elif class_name == 'VariableExprContext':
            # Odwołanie do pamięci: X[i]
            return self._evaluate_memory_ref(ctx.memoryRef())
        
        elif class_name == 'AtomExprContext':
            # Literał liczbowy
            return self._evaluate_value(ctx.value())
        
        else:
            # Fallback dla nierozpoznanych typów
            return self._fallback_evaluate(ctx)
    
    def _fallback_evaluate(self, ctx) -> float:
        """Fallback dla nierozpoznanych wyrażeń"""
        if hasattr(ctx, 'memoryRef') and ctx.memoryRef():
            return self._evaluate_memory_ref(ctx.memoryRef())
        elif hasattr(ctx, 'value') and ctx.value():
            return self._evaluate_value(ctx.value())
        elif hasattr(ctx, 'expression'):
            exprs = ctx.expression()
            if isinstance(exprs, list) and len(exprs) > 0:
                return self._evaluate_expression(exprs[0])
            elif exprs is not None:
                return self._evaluate_expression(exprs)
        return 0.0
    
    def _evaluate_memory_ref(self, ctx) -> float:
        """Pobiera wartość z pamięci X[i]"""
        index = int(ctx.INT().getText())
        if 0 <= index < len(self.memory):
            return float(self.memory[index])
        return 0.0
    
    def _evaluate_value(self, ctx) -> float:
        """Parsuje wartość liczbową (int lub float)"""
        if ctx.FLOAT():
            return float(ctx.FLOAT().getText())
        else:
            return float(ctx.INT().getText())
    
    def reset(self):
        """Resetuje interpreter do stanu początkowego"""
        self.memory = [0.0] * len(self.memory)
        self._execution_generator = None
    
    def set_memory(self, index: int, value: float):
        """Ustawia wartość w pamięci (do debugowania/testów)"""
        if 0 <= index < len(self.memory):
            self.memory[index] = float(value)
    
    def get_memory(self, index: int) -> float:
        """Pobiera wartość z pamięci"""
        if 0 <= index < len(self.memory):
            return self.memory[index]
        return 0.0
    
    def dump_memory(self, count: int = 10) -> list:
        """Zwraca pierwsze N komórek pamięci (do debugowania)"""
        return self.memory[:min(count, len(self.memory))]


class SRAPLErrorListener:
    """Listener do zbierania błędów parsowania"""
    
    def __init__(self):
        self.errors = []
    
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"Linia {line}:{column} - {msg}")
    
    def reportAmbiguity(self, *args):
        pass
    
    def reportAttemptingFullContext(self, *args):
        pass
    
    def reportContextSensitivity(self, *args):
        pass
```

### Plik: `interpreter.py` (zaktualizowany)

```python
"""
Wrapper interpretera kompatybilny z istniejącym kodem automaton.py
"""

from srapl_interpreter import SRAPLInterpreter


class Interpreter:
    """
    Adapter dla SRAPLInterpreter zachowujący kompatybilność
    z istniejącym kodem.
    """
    
    def __init__(self, program_code: str, memory_size: int = 64):
        """
        Args:
            program_code: Kod źródłowy SRAPL lub obiekt AST (dla kompatybilności)
        """
        if isinstance(program_code, str):
            self._interpreter = SRAPLInterpreter(program_code, memory_size)
            self.program = program_code
        else:
            # Stary kod mógł przekazywać AST - obsługa legacy
            self._interpreter = None
            self.program = program_code
        
        self.memory = [0.0] * memory_size
    
    @property
    def parts_scales(self) -> list:
        """Skale części z sekcji $PARTS"""
        if self._interpreter:
            return self._interpreter.get_parts_scales()
        return []
    
    def run_step(self, robot) -> tuple:
        """
        Wykonuje jeden krok programu.
        
        Returns:
            Tuple (func_id, args) określający akcję do wykonania
        """
        if self._interpreter is None:
            # Fallback dla starego kodu
            return (0, [])
        
        # Synchronizacja pamięci
        self._interpreter.memory = robot.memory
        
        # Wykonanie kroku
        func_id, args = self._interpreter.run_step()
        
        # Synchronizacja z powrotem
        robot.memory = self._interpreter.memory
        self.memory = self._interpreter.memory
        
        return func_id, args
    
    def reset(self):
        """Resetuje interpreter"""
        if self._interpreter:
            self._interpreter.reset()
        self.memory = [0.0] * len(self.memory)
```

---

## Instrukcja generowania plików ANTLR

### 1. Instalacja ANTLR4

```bash
# Instalacja runtime Pythona
pip install antlr4-python3-runtime

# Pobranie narzędzia ANTLR (wymagana Java)
curl -O https://www.antlr.org/download/antlr-4.13.1-complete.jar

# Opcjonalnie: alias
alias antlr4='java -jar /ścieżka/do/antlr-4.13.1-complete.jar'
```

### 2. Generowanie plików Pythona

```bash
# W katalogu z plikiem SRAPL.g4
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor SRAPL.g4

# Lub z aliasem:
antlr4 -Dlanguage=Python3 -visitor SRAPL.g4
```

To wygeneruje pliki:
- `SRAPLLexer.py`
- `SRAPLParser.py`
- `SRAPLListener.py`
- `SRAPLVisitor.py`

---

## Przykładowe programy testowe

### Program 1: `test_simple.srapl` - Prosty program

```
$PARTS:
1.0, 1.0, 1.0;

$PROGRAMM
# Prosty program - zawsze wykonuje f_1
f_1(1.0, 2.0);
```

### Program 2: `test_conditions.srapl` - Warunki i wyrażenia

```
$PARTS:
1.0, 2.0, 1.5, 0.5;

$PROGRAMM
# X[0] = energia, X[1] = odległość do celu

# Jeśli mamy dużo energii (>50)
IF (X[0] - 50.0) {
    # Jeśli cel blisko (<10)
    IF (10.0 - X[1]) {
        # Skanuj
        f_2(1.0);
    }
    # W przeciwnym razie jedź
    f_1(0.0, 5.0);
}

# Mało energii - odpoczywaj
f_0();
```

### Program 3: `test_loop.srapl` - Pętla z REDO

```
$PARTS:
1.0, 1.0;

$PROGRAMM
# Pętla zliczająca
X[0] = 0.0;

{
    X[0] = X[0] + 1.0;
    
    # Powtarzaj dopóki X[0] < 5
    IF (5.0 - X[0]) {
        REDO;
    }
}

# Po pętli X[0] == 5
f_1(X[0], 10.0);
```

### Program 4: `test_math.srapl` - Wyrażenia matematyczne

```
$PARTS:
1.0, 2.5, 0.7;

$PROGRAMM
# Test operacji matematycznych
X[0] = 10.0;
X[1] = 3.0;
X[2] = (X[0] + X[1]) * 2.0;           # = 26.0
X[3] = X[0] / X[1];                    # = 3.333...
X[4] = 2.0 ** 3.0;                     # = 8.0
X[5] = X[2] - (X[3] + X[4]);           # = 26 - 11.33 = 14.67

f_1(X[5], X[4]);
```

### Program 5: `test_complex.srapl` - Złożony scenariusz

```
$PARTS:
1.0, 3.0, 5.3, 0.7, 0.0, 0.0, 1.8;

$PROGRAMM
# X[0] - energia
# X[1] - odległość do przeszkody
# X[2] - tryb (0=szukaj, 1=unikaj, 2=zbieraj)

IF (X[0] - 10.0) {
    # Mamy energię > 10
    
    IF (5.0 - X[1]) {
        # Przeszkoda bliżej niż 5 jednostek
        X[2] = 1.0;
        f_2(90.0);  # Skręt/skan
    }
    
    # Sprawdź tryb
    IF (X[2] - 0.5) {
        IF (1.5 - X[2]) {
            # Tryb unikania (X[2] == 1)
            f_1(1.0, 2.0);
        }
        # Tryb zbierania (X[2] == 2)
        f_3(1.0);
    }
    
    # Tryb szukania (X[2] == 0)
    f_1(0.0, 1.0);
}

# Energii mało - ładowanie
X[5] = X[0] * 1.1;
f_0();
```

---

## Skrypt testowy

### Plik: `test_interpreter.py`

```python
#!/usr/bin/env python3
"""
Skrypt do testowania interpretera SRAPL
"""

import sys
import os

# Dodaj katalog z wygenerowanymi plikami ANTLR
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from srapl_interpreter import SRAPLInterpreter


def test_simple():
    """Test prostego programu"""
    print("=" * 50)
    print("TEST: Prosty program")
    print("=" * 50)
    
    code = """
$PARTS:
1.0, 2.0, 1.5;

$PROGRAMM
f_1(10.0, 20.0);
"""
    
    interp = SRAPLInterpreter(code)
    
    print(f"Skale części: {interp.get_parts_scales()}")
    
    func_id, args = interp.run_step()
    print(f"Wywołano: f_{func_id}({args})")
    
    assert func_id == 1
    assert args == [10.0, 20.0]
    print("✓ OK\n")


def test_expressions():
    """Test wyrażeń matematycznych"""
    print("=" * 50)
    print("TEST: Wyrażenia matematyczne")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = 10.0;
X[1] = 3.0;
X[2] = (X[0] + X[1]) * 2.0;
X[3] = X[0] / X[1];
X[4] = 2.0 ** 3.0;
f_0();
"""
    
    interp = SRAPLInterpreter(code)
    interp.run_step()
    
    print(f"X[0] = {interp.get_memory(0)} (oczekiwano: 10.0)")
    print(f"X[1] = {interp.get_memory(1)} (oczekiwano: 3.0)")
    print(f"X[2] = {interp.get_memory(2)} (oczekiwano: 26.0)")
    print(f"X[3] = {interp.get_memory(3):.4f} (oczekiwano: 3.3333)")
    print(f"X[4] = {interp.get_memory(4)} (oczekiwano: 8.0)")
    
    assert abs(interp.get_memory(0) - 10.0) < 0.001
    assert abs(interp.get_memory(2) - 26.0) < 0.001
    assert abs(interp.get_memory(3) - 3.3333) < 0.01
    assert abs(interp.get_memory(4) - 8.0) < 0.001
    print("✓ OK\n")


def test_conditions():
    """Test instrukcji warunkowych"""
    print("=" * 50)
    print("TEST: Instrukcje warunkowe")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = 100.0;
X[1] = 3.0;

IF (X[0] - 50.0) {
    X[10] = 1.0;
    
    IF (10.0 - X[1]) {
        X[11] = 1.0;
        f_2(1.0);
    }
    f_1(1.0);
}

f_0();
"""
    
    interp = SRAPLInterpreter(code)
    func_id, args = interp.run_step()
    
    print(f"X[10] = {interp.get_memory(10)} (oczekiwano: 1.0 - warunek zewn. spełniony)")
    print(f"X[11] = {interp.get_memory(11)} (oczekiwano: 1.0 - warunek wewn. spełniony)")
    print(f"Wywołano: f_{func_id}({args})")
    
    assert interp.get_memory(10) == 1.0
    assert interp.get_memory(11) == 1.0
    assert func_id == 2  # Pierwszy if wewnątrz if-a
    print("✓ OK\n")


def test_condition_false():
    """Test warunku niespełnionego"""
    print("=" * 50)
    print("TEST: Warunek niespełniony")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = 5.0;

IF (X[0] - 50.0) {
    X[10] = 1.0;
    f_1(1.0);
}

f_0();
"""
    
    interp = SRAPLInterpreter(code)
    func_id, args = interp.run_step()
    
    print(f"X[10] = {interp.get_memory(10)} (oczekiwano: 0.0 - warunek niespełniony)")
    print(f"Wywołano: f_{func_id} (oczekiwano: f_0)")
    
    assert interp.get_memory(10) == 0.0
    assert func_id == 0
    print("✓ OK\n")


def test_redo():
    """Test pętli REDO"""
    print("=" * 50)
    print("TEST: Pętla REDO")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = 0.0;

{
    X[0] = X[0] + 1.0;
    
    IF (5.0 - X[0]) {
        REDO;
    }
}

f_1(X[0]);
"""
    
    interp = SRAPLInterpreter(code)
    func_id, args = interp.run_step()
    
    print(f"X[0] = {interp.get_memory(0)} (oczekiwano: 5.0)")
    print(f"Wywołano: f_{func_id}({args})")
    
    assert interp.get_memory(0) == 5.0
    assert func_id == 1
    assert args[0] == 5.0
    print("✓ OK\n")


def test_resume():
    """Test wznowienia programu po wywołaniu funkcji"""
    print("=" * 50)
    print("TEST: Wznowienie wykonania")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = 1.0;
f_1(1.0);
X[0] = 2.0;
f_2(2.0);
X[0] = 3.0;
f_3(3.0);
"""
    
    interp = SRAPLInterpreter(code)
    
    # Krok 1
    func_id, args = interp.run_step()
    print(f"Krok 1: f_{func_id}({args}), X[0]={interp.get_memory(0)}")
    assert func_id == 1
    assert interp.get_memory(0) == 1.0
    
    # Krok 2 - kontynuacja
    func_id, args = interp.run_step()
    print(f"Krok 2: f_{func_id}({args}), X[0]={interp.get_memory(0)}")
    assert func_id == 2
    assert interp.get_memory(0) == 2.0
    
    # Krok 3 - kontynuacja
    func_id, args = interp.run_step()
    print(f"Krok 3: f_{func_id}({args}), X[0]={interp.get_memory(0)}")
    assert func_id == 3
    assert interp.get_memory(0) == 3.0
    
    # Krok 4 - restart od początku (pętla)
    func_id, args = interp.run_step()
    print(f"Krok 4 (restart): f_{func_id}({args}), X[0]={interp.get_memory(0)}")
    assert func_id == 1
    
    print("✓ OK\n")


def test_restart():
    """Test instrukcji RESTART"""
    print("=" * 50)
    print("TEST: Instrukcja RESTART")
    print("=" * 50)
    
    code = """
$PARTS:
1.0;

$PROGRAMM
X[0] = X[0] + 1.0;

IF (3.0 - X[0]) {
    RESTART;
}

f_1(X[0]);
"""
    
    interp = SRAPLInterpreter(code)
    func_id, args = interp.run_step()
    
    print(f"X[0] = {interp.get_memory(0)} (oczekiwano: 3.0)")
    print(f"Wywołano: f_{func_id}({args})")
    
    assert interp.get_memory(0) == 3.0
    assert args[0] == 3.0
    print("✓ OK\n")


def test_from_file(filename: str):
    """Test programu z pliku"""
    print("=" * 50)
    print(f"TEST: Plik {filename}")
    print("=" * 50)
    
    with open(filename, 'r') as f:
        code = f.read()
    
    print("Kod źródłowy:")
    print("-" * 30)
    print(code)
    print("-" * 30)
    
    interp = SRAPLInterpreter(code)
    
    print(f"Skale części: {interp.get_parts_scales()}")
    print()
    
    # Wykonaj kilka kroków
    for i in range(5):
        func_id, args = interp.run_step()
        print(f"Krok {i+1}: f_{func_id}({args})")
        print(f"  Pamięć: {interp.dump_memory(10)}")
    
    print()


def interactive_mode():
    """Tryb interaktywny do debugowania"""
    print("=" * 50)
    print("TRYB INTERAKTYWNY")
    print("=" * 50)
    print("Polecenia:")
    print("  load <plik>  - wczytaj program z pliku")
    print("  step         - wykonaj jeden krok")
    print("  mem [n]      - pokaż pamięć (domyślnie 10 komórek)")
    print("  set i v      - ustaw X[i] = v")
    print("  reset        - zresetuj interpreter")
    print("  quit         - wyjdź")
    print()
    
    interp = None
    
    while True:
        try:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
            
            if cmd[0] == "quit":
                break
            
            elif cmd[0] == "load":
                if len(cmd) < 2:
                    print("Użycie: load <plik>")
                    continue
                with open(cmd[1], 'r') as f:
                    code = f.read()
                interp = SRAPLInterpreter(code)
                print(f"Wczytano. Skale części: {interp.get_parts_scales()}")
            
            elif cmd[0] == "step":
                if interp is None:
                    print("Najpierw wczytaj program (load)")
                    continue
                func_id, args = interp.run_step()
                print(f"→ f_{func_id}({args})")
            
            elif cmd[0] == "mem":
                if interp is None:
                    print("Najpierw wczytaj program")
                    continue
                n = int(cmd[1]) if len(cmd) > 1 else 10
                mem = interp.dump_memory(n)
                for i, v in enumerate(mem):
                    if v != 0:
                        print(f"  X[{i}] = {v}")
            
            elif cmd[0] == "set":
                if interp is None or len(cmd) < 3:
                    print("Użycie: set <indeks> <wartość>")
                    continue
                interp.set_memory(int(cmd[1]), float(cmd[2]))
                print(f"X[{cmd[1]}] = {cmd[2]}")
            
            elif cmd[0] == "reset":
                if interp:
                    interp.reset()
                    print("Zresetowano")
            
            else:
                print(f"Nieznane polecenie: {cmd[0]}")
        
        except KeyboardInterrupt:
            print()
            break
        except Exception as e:
            print(f"Błąd: {e}")


def main():
    """Główna funkcja testowa"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "-i":
            interactive_mode()
        else:
            test_from_file(sys.argv[1])
    else:
        # Uruchom wszystkie testy jednostkowe
        test_simple()
        test_expressions()
        test_conditions()
        test_condition_false()
        test_redo()
        test_resume()
        test_restart()
        
        print("=" * 50)
        print("WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
        print("=" * 50)


if __name__ == "__main__":
    main()
```

---

## Jak uruchomić i debugować

### 1. Wygeneruj pliki ANTLR

```bash
# W katalogu projektu
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor SRAPL.g4
```

### 2. Uruchom testy jednostkowe

```bash
python test_interpreter.py
```

Oczekiwany output:
```
==================================================
TEST: Prosty program
==================================================
Skale części: [1.0, 2.0, 1.5]
Wywołano: f_1([10.0, 20.0])
✓ OK

... (więcej testów)

==================================================
WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!
==================================================
```

### 3. Testuj plik programu

```bash
python test_interpreter.py test_simple.srapl
```

### 4. Tryb interaktywny (debugowanie)

```bash
python test_interpreter.py -i
```

Przykładowa sesja:
```
> load test_conditions.srapl
Wczytano. Skale części: [1.0, 2.0, 1.5, 0.5]
> set 0 100.0
X[0] = 100.0
> set 1 3.0
X[1] = 3.0
> step
→ f_2([1.0])
> mem
  X[0] = 100.0
  X[1] = 3.0
> step
→ f_1([0.0, 5.0])
> quit
```

### 5. Integracja z automatem

```python
from automaton import Automaton
from parts import Engine, Scanner, Storage

# Kod programu
program = """
$PARTS:
1.0, 1.5, 2.0;

$PROGRAMM
IF (X[0] - 10.0) {
    f_1(0.0, 5.0);
}
f_0();
"""

# Genom części
parts_genome = [
    (Engine, 1.0),
    (Scanner, 1.5),
    (Storage, 2.0),
]

# Stwórz automat
robot = Automaton(program, parts_genome, world=None, position=(0, 0))

# Ustaw stan początkowy
robot.memory[0] = 50.0  # energia

# Wykonaj krok
robot.update()
```

---

## Podsumowanie zmian

| Plik | Zmiany |
|------|--------|
| `srapl_interpreter.py` | **NOWY** - główny interpreter z generatorami |
| `interpreter.py` | Zaktualizowany jako adapter |
| `test_interpreter.py` | **NOWY** - testy i debugger |
| `SRAPL.g4` | Bez zmian (gramatyka jest poprawna) |

Interpreter obsługuje wszystkie elementy specyfikacji:
- ✅ Sekcja `$PARTS` z skalami
- ✅ Sekcja `$PROGRAMM` z kodem
- ✅ Wyrażenia matematyczne (+, -, *, /, **)
- ✅ Odwołania do pamięci X[i]
- ✅ Przypisania
- ✅ Warunki IF (wykonanie gdy > 0)
- ✅ Bloki kodu
- ✅ REDO (powtórzenie bloku)
- ✅ RESTART (restart programu)
- ✅ Wywołania funkcji f_n (kończą krok)
- ✅ Wznowienie po wywołaniu funkcji
- ✅ Pętla główna (restart po końcu programu)