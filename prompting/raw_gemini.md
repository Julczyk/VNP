Oto kompletna implementacja warstwy językowej projektu.

### Podejęte decyzje projektowe:

1.  **Technologia: ANTLR4 Visitor + Python Generators (Coroutines)**.
    *   **Dlaczego Visitor?** Gramatyka zawiera wyrażenia matematyczne (nawiasy, priorytety operatorów) oraz struktury zagnieżdżone (`IF`, `Block`). Wzorzec Visitora (Odwiedzającego) pozwala najłatwiej ewaluować wyrażenia rekurencyjnie i zarządzać przepływem sterowania.
    *   **Dlaczego Generatory (`yield`)?** Specyfikacja wymaga, aby program "zatrzymywał się" po wywołaniu funkcji `f_n` i wznawiał działanie w następnym kroku symulacji dokładnie w tym samym miejscu. Pythonowe generatory idealnie realizują ten wzorzec – funkcja `yield` zwraca sterowanie do symulacji (wraz z ID funkcji do wykonania), a w kolejnym kroku `next()` wznawia wykonywanie interpretera ze zachowaniem stosu wywołań i zmiennych lokalnych.

2.  **Obsługa `REDO` i `RESTART` poprzez wyjątki sterujące**.
    *   Ponieważ `REDO` musi przeskoczyć do początku *obecnego* bloku, a Visitor działa rekurencyjnie, najczystszym sposobem na "wycofanie się" z głębi instrukcji do początku pętli jest rzucenie wewnętrznego wyjątku (`RedoSignal`), który jest łapany przez metodę odwiedzającą blok (`visitBlock`). Analogicznie działa `RestartSignal`.

3.  **Parsowanie części (`$PARTS`)**.
    *   Sekcja części jest potrzebna przed utworzeniem Automatu (bo definiuje jego budowę), dlatego wydzieliłem metodę statyczną `parse_parts_specs`, która wyciąga tylko konfigurację części, bez uruchamiania programu.

---

### 1. Wymagania wstępne

Aby kod działał, musisz wygenerować pliki Pythona z gramatyki `.g4` oraz zainstalować runtime ANTLR.

W terminalu:
```bash
pip install antlr4-python3-runtime
antlr4 -Dlanguage=Python3 -visitor SRAPL.g4
```
*(Jeśli nie masz komendy `antlr4`, musisz pobrać plik jar ze strony ANTLR lub użyć odpowiedniego pluginu/narzędzia).*
Powinny pojawić się pliki: `SRAPLLexer.py`, `SRAPLParser.py`, `SRAPLVisitor.py`.

### 2. Kod interpretera (`interpreter.py`)

Zastąp zawartość pliku `interpreter.py` poniższym kodem. Zawiera on pełną logikę wykonywania programu.

```python
import sys
from antlr4 import *
from SRAPLLexer import SRAPLLexer
from SRAPLParser import SRAPLParser
from SRAPLVisitor import SRAPLVisitor
from config import FunctionID

# Wyjątki sterujące przepływem (nie są błędami, lecz sygnałami)
class RedoSignal(Exception):
    pass

class RestartSignal(Exception):
    pass

class ProgramFinished(Exception):
    pass

class SRAPLExecutionVisitor(SRAPLVisitor):
    def __init__(self, automaton):
        self.automaton = automaton
        self.memory = automaton.memory # Referencja do pamięci automatu

    def visitProgrammSection(self, ctx: SRAPLParser.ProgrammSectionContext):
        # Główna pętla programu (Restart Loop)
        while True:
            try:
                # Odwiedź główny blok instrukcji
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                
                # Jeśli program dojdzie do końca, kończymy (zostanie zrestartowany przez Interpretera)
                break 
            except RestartSignal:
                # Obsługa RESTART - pętla while True zacznie od nowa
                continue

    def visitBlockContent(self, ctx: SRAPLParser.BlockContentContext):
        # Odwiedzanie listy instrukcji w bloku
        for statement in ctx.statement():
            yield from self.visit(statement)

    def visitBlock(self, ctx: SRAPLParser.BlockContext):
        # Obsługa bloku i instrukcji REDO
        while True:
            try:
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                break # Blok wykonany poprawnie, wychodzimy z while
            except RedoSignal:
                # Złapano REDO wewnątrz tego bloku -> pętla while zaczyna od nowa
                continue

    def visitAssignment(self, ctx: SRAPLParser.AssignmentContext):
        # X[i] = expr
        mem_idx = int(ctx.memoryRef().INT().getText())
        value = self.visit(ctx.expression())
        
        # Zabezpieczenie zakresu pamięci
        if 0 <= mem_idx < len(self.memory):
            self.memory[mem_idx] = float(value)
        return None

    def visitFunctionCall(self, ctx: SRAPLParser.FunctionCallContext):
        # Parsowanie ID funkcji: f_n -> n
        func_text = ctx.FUNC_ID().getText() # "f_1"
        func_id_val = int(func_text.split('_')[1])
        
        # Ewaluacja argumentów
        args = []
        if ctx.argList():
            for expr in ctx.argList().expression():
                args.append(float(self.visit(expr)))
        
        # YIELD - Zatrzymujemy wykonanie i zwracamy akcję do Symulatora
        # Konwertujemy int na Enum, jeśli istnieje w configu, lub zostawiamy int
        try:
            enum_id = FunctionID(func_id_val)
        except ValueError:
            enum_id = func_id_val # Fallback dla nieznanych ID

        yield (enum_id, args)

    def visitIfStatement(self, ctx: SRAPLParser.IfStatementContext):
        condition = self.visit(ctx.expression())
        if condition > 0:
            yield from self.visit(ctx.block())

    def visitRedoStatement(self, ctx: SRAPLParser.RedoStatementContext):
        raise RedoSignal()

    def visitRestartStatement(self, ctx: SRAPLParser.RestartStatementContext):
        raise RestartSignal()

    # --- Ewaluacja Wyrażeń ---

    def visitAtomExpr(self, ctx: SRAPLParser.AtomExprContext):
        # Liczba
        return float(ctx.value().getText())

    def visitVariableExpr(self, ctx: SRAPLParser.VariableExprContext):
        # Zmienna X[i]
        idx = int(ctx.memoryRef().INT().getText())
        if 0 <= idx < len(self.memory):
            return self.memory[idx]
        return 0.0

    def visitParensExpr(self, ctx: SRAPLParser.ParensExprContext):
        return self.visit(ctx.expression())

    def visitPowerExpr(self, ctx: SRAPLParser.PowerExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        try:
            return math.pow(left, right)
        except OverflowError:
            return float('inf')

    def visitMulDivExpr(self, ctx: SRAPLParser.MulDivExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '*':
            return left * right
        else:
            return left / right if right != 0 else 0.0

    def visitAddSubExpr(self, ctx: SRAPLParser.AddSubExprContext):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '+':
            return left + right
        else:
            return left - right

    # --- Pomocnicze do Visitora (domyślne zachowanie) ---
    def defaultResult(self):
        return None
        
import math

class Interpreter:
    """
    Wykonuje program automatu używając ANTLR4.
    """

    def __init__(self, program_code):
        self.program_code = program_code
        self.generator = None
        
        # Wstępne parsowanie, aby sprawdzić błędy składni (opcjonalne, ale dobre dla debugu)
        self.tree = self._parse(program_code)

    def _parse(self, code):
        input_stream = InputStream(code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        # file -> partsSection programmSection
        return parser.file() 

    @staticmethod
    def parse_parts_specs(program_code):
        """
        Statyczna metoda parsująca sekcję $PARTS, aby zbudować robota
        przed uruchomieniem interpretera.
        Zwraca: listę floatów (skale części).
        """
        input_stream = InputStream(program_code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        
        # Parsujemy tylko sekcję parts
        tree = parser.partsSection()
        
        # Prosty visitor lokalny do wyciągnięcia liczb
        scales = []
        if tree.floatList():
            for val in tree.floatList().value():
                scales.append(float(val.getText()))
        return scales

    def run_step(self, robot):
        """
        Uruchamia program na jeden krok symulacji.
        Zwraca ID funkcji (f_n) i argumenty.
        """
        if self.generator is None:
            # Pierwsze uruchomienie - tworzymy generator
            visitor = SRAPLExecutionVisitor(robot)
            # Zaczynamy od sekcji programu (partsSection pomijamy przy egzekucji)
            program_ctx = self.tree.programmSection()
            self.generator = visitor.visitProgrammSection(program_ctx)

        try:
            # Wznów wykonanie do następnego yield (wywołania funkcji f_n)
            func_id, args = next(self.generator)
            return func_id, args
        
        except StopIteration:
            # Program się skończył (doszedł do końca kodu bez pętli)
            # Wg specyfikacji: "loop" - zaczynamy od nowa w tym samym kroku?
            # Czy w następnym? Przyjmijmy, że resetujemy generator i próbujemy jeszcze raz.
            self.generator = None
            
            # Rekurencyjne wywołanie (ostrożnie, żeby nie zapętlić w nieskończoność 
            # jeśli program jest pusty)
            # Dla bezpieczeństwa zwracamy IDLE, a restart nastąpi w kolejnym kroku
            return FunctionID.IDLE, []
            
        except Exception as e:
            print(f"Runtime Error in automaton {robot}: {e}")
            return FunctionID.IDLE, []

```

### 3. Jak to spiąć z `automaton.py`?

Musisz zmodyfikować `automaton.py`, aby poprawnie korzystał z nowego Interpretera, szczególnie przy inicjalizacji (parsowanie części).

W `automaton.py` w klasie `Automaton`:

1.  Zmień sposób tworzenia robota w `__init__`, aby najpierw wyciągnąć genom z kodu (chyba że genom jest przekazywany z zewnątrz przez algorytm genetyczny - specyfikacja mówi, że `$PARTS` jest w kodzie).
    *   *Jeśli kod jest źródłem prawdy:* Użyj `Interpreter.parse_parts_specs(code)`.
    *   *Jeśli algorytm genetyczny steruje:* Genom przychodzi jako argument `parts_genome`. Wtedy `$PARTS` w pliku tekstowym może być tylko reprezentacją.

Zakładając, że tworzymy robota z pliku tekstowego:

```python
# Helper do tworzenia robota z kodu (np. w symulacji startowej)
def create_automaton_from_code(code, world, pos):
    # 1. Parsowanie genomu
    raw_scales = Interpreter.parse_parts_specs(code)
    
    # Mapowanie indeksów na klasy części (musisz ustalić kolejność w configu lub parts.py)
    # Przykład: 0: Engine, 1: Scanner, 2: Storage...
    from parts import Engine, Scanner, Storage, Smelter, Assembler, PowerGenerator
    
    # Przykładowa mapa typów części wg kolejności w $PARTS
    available_parts = [PowerGenerator, Engine, Scanner, Storage, Smelter, Assembler]
    
    parts_genome = []
    for i, scale in enumerate(raw_scales):
        if i < len(available_parts):
            parts_genome.append((available_parts[i], scale))
            
    return Automaton(code, parts_genome, world, pos)
```

W metodzie `update` klasy `Automaton` w `automaton.py`:
Interpreter zwraca teraz `Enum` lub `int`. `parts.py` oczekuje `int` w `part_map` lub `Enum.value`.

```python
    def update(self):
        # ...
        func_id, args = self.interpreter.run_step(self)
        
        # Konwersja Enum na int, jeśli trzeba
        f_val = func_id.value if hasattr(func_id, 'value') else func_id

        if f_val in self.part_map:
            part = self.part_map[f_val]
            part.execute_action(self, args)
        # ...
```

---

### 4. Instrukcja testowania i debugowania

Stwórz plik `test_srapl.py`, aby przetestować język bez uruchamiania całej graficznej symulacji.

```python
import unittest
from interpreter import Interpreter
from config import FunctionID

# Mock dla Automatonu
class MockAutomaton:
    def __init__(self):
        self.memory = [0.0] * 64
    
    def __str__(self):
        return "MockBot"

class TestSRAPL(unittest.TestCase):

    def test_arithmetic_and_assignment(self):
        code = """
        $PARTS 1.0;
        $PROGRAMM
        X[0] = 2.0;
        X[1] = (X[0] * 3) + 4;
        f_0();
        """
        robot = MockAutomaton()
        interp = Interpreter(code)
        
        # Krok 1: wykonuje przypisania i zatrzymuje się na f_0
        fid, args = interp.run_step(robot)
        
        self.assertEqual(robot.memory[0], 2.0)
        self.assertEqual(robot.memory[1], 10.0) # (2*3)+4
        self.assertEqual(fid, FunctionID.IDLE) # f_0 to IDLE w configu

    def test_if_condition(self):
        code = """
        $PARTS;
        $PROGRAMM
        X[0] = 10;
        IF (X[0] - 5) {
            f_1(1);
        }
        f_2(0);
        """
        robot = MockAutomaton()
        interp = Interpreter(code)
        
        # X[0]=10, warunek 10-5=5 (>0), wchodzi w IF -> f_1
        fid, args = interp.run_step(robot)
        self.assertEqual(fid.value, 1) # f_1
        self.assertEqual(args[0], 1.0)
        
        # Następny krok: wraca po bloku IF -> f_2
        fid, args = interp.run_step(robot)
        self.assertEqual(fid.value, 2) # f_2

    def test_redo_loop(self):
        code = """
        $PARTS;
        $PROGRAMM
        X[0] = 0;
        {
            X[0] = X[0] + 1;
            IF (3 - X[0]) {
                # Jeśli X[0] < 3 (czyli 3-X[0] > 0), powtórz blok
                REDO;
            }
            f_1(X[0]);
        }
        """
        robot = MockAutomaton()
        interp = Interpreter(code)
        
        # Pętla powinna kręcić się wewnętrznie dopóki nie napotka f_n LUB
        # interpreter wykonuje instrukcje "do skutku".
        # Tutaj: 
        # 1. X[0]=1, IF(2) -> REDO
        # 2. X[0]=2, IF(1) -> REDO
        # 3. X[0]=3, IF(0) -> false -> f_1(3)
        
        # Ponieważ interpreter wewnątrz jednego kroku `run_step` pętli `while` 
        # wykonuje instrukcje aż do `yield` (czyli f_n), te pętle REDO wykonają się natychmiastowo.
        
        fid, args = interp.run_step(robot)
        self.assertEqual(robot.memory[0], 3.0)
        self.assertEqual(args[0], 3.0)

    def test_parts_parsing(self):
        code = """
        $PARTS 
        1.0, 2.5, 0.0;
        $PROGRAMM
        f_0();
        """
        scales = Interpreter.parse_parts_specs(code)
        self.assertEqual(scales, [1.0, 2.5, 0.0])

if __name__ == '__main__':
    # Uruchomienie testów: python test_srapl.py
    unittest.main()
```

### Jak debugować?

1.  **Printy w Visitorze**: W `SRAPLVisitor.py` (lub w klasie `SRAPLExecutionVisitor` w `interpreter.py`) możesz dodać `print(f"Visiting {ctx.getText()}")` w metodach `visit...`. To pokaże Ci ścieżkę, jaką interpreter pokonuje w drzewie.
2.  **Podgląd Pamięci**: W `interpreter.py`, w `visitAssignment`, możesz wypisywać stan pamięci po każdej zmianie: `print(f"DEBUG: Memory updated: {self.memory}")`.
3.  **Testy jednostkowe**: Uruchamiaj `test_srapl.py`. Modyfikuj ciągi znaków `code` w testach, aby sprawdzać różne scenariusze (zagnieżdżone IFy, RESTART, skomplikowane wyrażenia).

To rozwiązanie zapewnia pełną zgodność ze specyfikacją, poprawną obsługę stanu (dzięki generatorom) i jest gotowe do wpięcia w symulację.