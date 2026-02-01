"""
SRAPL Interpreter - Interpreter języka SRAPL dla automatów samoreplikujących.

Wykorzystuje ANTLR4 do parsowania i implementuje wzorzec Visitor z generatorami
dla krokowego wykonania programu (jeden krok symulacji = jedno wywołanie f_n).
"""

import math
import logging
import random
from pathlib import Path

from antlr4 import InputStream, CommonTokenStream

# Import ANTLR4-generated files
import sys
sys.path.insert(0, str(Path(__file__).parent / 'sraplBase'))
from sraplBase.SRAPLLexer import SRAPLLexer
from sraplBase.SRAPLParser import SRAPLParser
from sraplBase.SRAPLVisitor import SRAPLVisitor

from config import FunctionID

# --- Konfiguracja logowania ---
logger = logging.getLogger('SRAPL')


# --- Wyjątki sterujące przepływem (sygnały, nie błędy) ---

class RedoSignal(Exception):
    """Sygnał REDO - powrót do początku bieżącego bloku."""
    pass


class RestartSignal(Exception):
    """Sygnał RESTART - powrót do początku programu."""
    pass


class ProgramFinished(Exception):
    """Sygnał zakończenia programu (doszedł do końca)."""
    pass


# --- Visitor wykonujący program ---

class SRAPLExecutionVisitor(SRAPLVisitor):
    """
    Visitor ANTLR4 wykonujący program SRAPL.

    Używa generatorów (yield) do zatrzymywania wykonania przy każdym
    wywołaniu funkcji f_n. Dzięki temu symulator może wykonać jedną
    akcję na krok symulacji.
    """

    def __init__(self, automaton, debug=False):
        self.automaton = automaton
        self.memory = automaton.memory  # Referencja do pamięci automatu (64 floaty)
        self.debug = debug

    def _log(self, message):
        """Pomocnicza metoda do logowania z kontekstem automatu."""
        if self.debug:
            pos = getattr(self.automaton, 'position', '?')
            logger.debug(f"[Automaton@{pos}] {message}")

    # --- Sekcja programu ---

    def visitProgrammSection(self, ctx: SRAPLParser.ProgrammSectionContext):
        """
        Główna pętla programu (obsługa RESTART).
        Program wykonuje się w pętli - po dojściu do końca zaczyna od nowa.
        """
        while True:
            try:
                self._log(">>> Program START")
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                self._log(">>> Program END (reached end of code)")
                # Program doszedł do końca - wracamy na początek
                continue
            except RestartSignal:
                self._log(">>> RESTART signal caught - restarting program")
                continue

    def visitBlockContent(self, ctx: SRAPLParser.BlockContentContext):
        """Odwiedzanie listy instrukcji w bloku."""
        for statement in ctx.statement():
            result = self.visit(statement)
            # Obsługa generatorów z zagnieżdżonych wywołań
            if hasattr(result, '__iter__') and hasattr(result, '__next__'):
                yield from result

    def visitBlock(self, ctx: SRAPLParser.BlockContext):
        """
        Blok kodu { ... } z obsługą REDO.
        REDO powoduje powrót do początku tego konkretnego bloku.
        """
        while True:
            try:
                self._log(">>> Block START")
                if ctx.blockContent():
                    yield from self.visit(ctx.blockContent())
                self._log(">>> Block END")
                break  # Blok wykonany poprawnie
            except RedoSignal:
                self._log(">>> REDO signal caught - restarting block")
                continue

    # --- Instrukcje ---

    def visitAssignment(self, ctx: SRAPLParser.AssignmentContext):
        """
        Przypisanie: X[i] = wyrażenie;
        """
        mem_idx = int(ctx.memoryRef().INT().getText())
        value = self.visit(ctx.expression())

        if 0 <= mem_idx < len(self.memory):
            old_value = self.memory[mem_idx]
            self.memory[mem_idx] = float(value)
            self._log(f"Assignment: X[{mem_idx}] = {value} (was {old_value})")
        else:
            self._log(f"Assignment ERROR: X[{mem_idx}] out of range (0-63)")

        return None

    def visitFunctionCall(self, ctx: SRAPLParser.FunctionCallContext):
        """
        Wywołanie funkcji: f_n(args);

        YIELD - zatrzymuje wykonanie i zwraca akcję do symulatora.
        Wywołanie dowolnej funkcji f_n kończy krok czasowy.
        """
        func_text = ctx.FUNC_ID().getText()  # "f_1"
        func_id_val = int(func_text.split('_')[1])

        # Ewaluacja argumentów
        args = []
        if ctx.argList():
            for expr in ctx.argList().expression():
                args.append(float(self.visit(expr)))

        self._log(f"Function call: {func_text}({args})")

        # Konwersja na Enum (jeśli istnieje)
        try:
            enum_id = FunctionID(func_id_val)
        except ValueError:
            enum_id = func_id_val  # Fallback dla nieznanych ID

        # YIELD - zwracamy kontrolę do symulatora
        yield (enum_id, args)

    def visitIfStatement(self, ctx: SRAPLParser.IfStatementContext):
        """
        Instrukcja warunkowa: IF(wyrażenie) { blok }
        Blok wykonuje się gdy wyrażenie > 0.
        """
        condition = self.visit(ctx.expression())
        self._log(f"IF condition: {condition} -> {'TRUE' if condition > 0 else 'FALSE'}")

        if condition > 0:
            result = self.visit(ctx.block())
            if hasattr(result, '__iter__') and hasattr(result, '__next__'):
                yield from result

    def visitRedoStatement(self, ctx: SRAPLParser.RedoStatementContext):
        """REDO - powrót do początku bieżącego bloku."""
        self._log("REDO statement")
        raise RedoSignal()

    def visitRestartStatement(self, ctx: SRAPLParser.RestartStatementContext):
        """RESTART - powrót do początku programu."""
        self._log("RESTART statement")
        raise RestartSignal()

    # --- Ewaluacja wyrażeń ---

    def visitAtomExpr(self, ctx: SRAPLParser.AtomExprContext):
        """Liczba (INT lub FLOAT)."""
        return float(ctx.value().getText())

    def visitVariableExpr(self, ctx: SRAPLParser.VariableExprContext):
        """Zmienna X[i]."""
        idx = int(ctx.memoryRef().INT().getText())
        if 0 <= idx < len(self.memory):
            return self.memory[idx]
        self._log(f"Variable ERROR: X[{idx}] out of range, returning 0.0")
        return 0.0

    def visitParensExpr(self, ctx: SRAPLParser.ParensExprContext):
        """Wyrażenie w nawiasach (expr)."""
        return self.visit(ctx.expression())

    def visitPowerExpr(self, ctx: SRAPLParser.PowerExprContext):
        """Potęgowanie: a ** b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        try:
            return math.pow(left, right)
        except (OverflowError, ValueError):
            return float('inf') if left > 0 else float('-inf')

    def visitMulDivExpr(self, ctx: SRAPLParser.MulDivExprContext):
        """Mnożenie/dzielenie: a * b, a / b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '*':
            return left * right
        else:
            return left / right if right != 0 else 0.0

    def visitAddSubExpr(self, ctx: SRAPLParser.AddSubExprContext):
        """Dodawanie/odejmowanie: a + b, a - b."""
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(1))
        op = ctx.getChild(1).getText()
        if op == '+':
            return left + right
        else:
            return left - right

    def defaultResult(self):
        return None


# --- Główna klasa interpretera ---

class SRAPLInterpreter:
    """
    Interpreter programów SRAPL.

    Odpowiada za:
    - Parsowanie kodu źródłowego
    - Krokowe wykonywanie programu (jeden krok = jedno f_n)
    - Import/export do plików .srl
    - Placeholder'y mutacji dla algorytmu genetycznego
    """

    def __init__(self, program_code: str, debug: bool = False):
        """
        Inicjalizuje interpreter z kodem programu.

        Args:
            program_code: Kod źródłowy SRAPL (tekst)
            debug: Włącz szczegółowe logowanie
        """
        self.program_code = program_code
        self.debug = debug
        self.generator = None

        # Parsowanie przy inicjalizacji (wykrycie błędów składni)
        self.tree = self._parse(program_code)

        # Cache sparsowanych części (dla optymalizacji)
        self._parts_cache = None

        if self.debug:
            logger.info(f"Interpreter initialized, code length: {len(program_code)} chars")

    @property
    def program(self) -> str:
        """Zwraca kod źródłowy programu (dla kompatybilności z reproduce())."""
        return self.program_code

    def _parse(self, code: str) -> SRAPLParser.FileContext:
        """Parsuje kod SRAPL i zwraca drzewo AST."""
        input_stream = InputStream(code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)
        return parser.file_()

    # --- Wykonywanie programu ---

    def run_step(self, automaton) -> tuple:
        """
        Wykonuje program do następnego wywołania funkcji f_n.

        Args:
            automaton: Obiekt automatu z pamięcią i częściami

        Returns:
            Tuple (FunctionID, list[float]) - ID funkcji i argumenty
        """
        if self.generator is None:
            # Pierwsze uruchomienie - tworzenie generatora
            visitor = SRAPLExecutionVisitor(automaton, debug=self.debug)
            program_ctx = self.tree.programmSection()
            self.generator = visitor.visitProgrammSection(program_ctx)
            if self.debug:
                logger.info("Created new execution generator")

        try:
            func_id, args = next(self.generator)
            if self.debug:
                logger.info(f"Step result: {func_id}, args={args}")
            return func_id, args

        except StopIteration:
            # Program się skończył (nie powinno się zdarzyć z nieskończoną pętlą)
            if self.debug:
                logger.warning("Program finished unexpectedly (StopIteration)")
            self.generator = None
            return FunctionID.IDLE, []

        except Exception as e:
            logger.error(f"Runtime error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            return FunctionID.IDLE, []

    def reset(self):
        """Resetuje stan interpretera (restartuje program od początku)."""
        self.generator = None
        if self.debug:
            logger.info("Interpreter reset")

    # --- Parsowanie sekcji części ---

    @staticmethod
    def parse_parts_specs(program_code: str) -> list[float]:
        """
        Parsuje sekcję $PARTS i zwraca listę skali części.

        Args:
            program_code: Kod źródłowy SRAPL

        Returns:
            Lista floatów - skale części w kolejności ID
        """
        input_stream = InputStream(program_code)
        lexer = SRAPLLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = SRAPLParser(stream)

        tree = parser.partsSection()

        scales = []
        if tree.floatList():
            for val in tree.floatList().value():
                scales.append(float(val.getText()))

        logger.debug(f"Parsed parts specs: {scales}")
        return scales

    def get_parts_specs(self) -> list[float]:
        """Zwraca sparsowane skale części (z cache)."""
        if self._parts_cache is None:
            self._parts_cache = self.parse_parts_specs(self.program_code)
        return self._parts_cache

    # --- Import/Export plików .srl ---

    @classmethod
    def from_file(cls, filepath: str, debug: bool = False) -> 'SRAPLInterpreter':
        """
        Wczytuje program z pliku .srl.

        Args:
            filepath: Ścieżka do pliku .srl
            debug: Włącz szczegółowe logowanie

        Returns:
            Nowa instancja SRAPLInterpreter
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        program_code = path.read_text(encoding='utf-8')
        logger.info(f"Loaded program from {filepath}")

        return cls(program_code, debug=debug)

    def to_file(self, filepath: str):
        """
        Zapisuje program do pliku .srl.

        Args:
            filepath: Ścieżka do pliku .srl
        """
        path = Path(filepath)
        path.write_text(self.program_code, encoding='utf-8')
        logger.info(f"Saved program to {filepath}")

    @staticmethod
    def load_program(filepath: str) -> str:
        """
        Wczytuje kod programu z pliku .srl (tylko tekst, bez tworzenia interpretera).

        Args:
            filepath: Ścieżka do pliku .srl

        Returns:
            Kod źródłowy programu
        """
        path = Path(filepath)
        return path.read_text(encoding='utf-8')

    @staticmethod
    def save_program(program_code: str, filepath: str):
        """
        Zapisuje kod programu do pliku .srl.

        Args:
            program_code: Kod źródłowy SRAPL
            filepath: Ścieżka do pliku .srl
        """
        path = Path(filepath)
        path.write_text(program_code, encoding='utf-8')
        logger.info(f"Saved program to {filepath}")

    # --- Placeholdery mutacji dla algorytmu genetycznego ---

    def mutate_expression(self, expr_str: str, mutation_rate: float = 0.1) -> str:
        """
        PLACEHOLDER: Mutacja pojedynczego wyrażenia.

        TODO: Implementacja mutacji wyrażeń:
        - Zmiana stałych liczbowych (dodanie szumu)
        - Zmiana operatorów (+, -, *, /)
        - Zmiana indeksów pamięci X[i]

        Args:
            expr_str: Wyrażenie jako string
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowane wyrażenie (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        return expr_str

    def mutate_value(self, value: float, mutation_rate: float = 0.1) -> float:
        """
        PLACEHOLDER: Mutacja wartości liczbowej.

        TODO: Implementacja mutacji wartości:
        - Dodanie szumu gaussowskiego
        - Mnożenie przez losowy czynnik
        - Zamiana na losową wartość

        Args:
            value: Wartość do zmutowania
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowana wartość (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        return value

    def mutate_memory_index(self, index: int, mutation_rate: float = 0.1) -> int:
        """
        PLACEHOLDER: Mutacja indeksu pamięci.

        TODO: Implementacja mutacji indeksów:
        - Przesunięcie o +/- 1
        - Losowy nowy indeks

        Args:
            index: Indeks pamięci (0-63)
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowany indeks (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        return index

    def mutate_function_args(self, args: list[float], mutation_rate: float = 0.1) -> list[float]:
        """
        PLACEHOLDER: Mutacja argumentów funkcji.

        TODO: Implementacja mutacji argumentów:
        - Mutacja poszczególnych wartości
        - Dodawanie/usuwanie argumentów (jeśli funkcja na to pozwala)

        Args:
            args: Lista argumentów
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowane argumenty (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        return args.copy()

    def mutate_parts_scales(self, scales: list[float], mutation_rate: float = 0.1) -> list[float]:
        """
        PLACEHOLDER: Mutacja skali części w sekcji $PARTS.

        TODO: Implementacja mutacji skal:
        - Dodanie szumu do poszczególnych skal
        - Ograniczenie do zakresu [0.0, 10.0]

        Args:
            scales: Lista skali części
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowane skale (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        return scales.copy()

    def mutate_program(self, mutation_rate: float = 0.1) -> str:
        """
        PLACEHOLDER: Mutacja całego programu.

        TODO: Implementacja pełnej mutacji programu:
        - Mutacja sekcji $PARTS (skale)
        - Mutacja wyrażeń
        - Mutacja stałych
        - Dodawanie/usuwanie instrukcji
        - Zmiana struktury IF/bloków

        Args:
            mutation_rate: Prawdopodobieństwo mutacji (0.0-1.0)

        Returns:
            Zmutowany kod programu (obecnie bez zmian)
        """
        # PLACEHOLDER - do rozwinięcia
        logger.debug(f"mutate_program called with rate={mutation_rate} (PLACEHOLDER)")
        return self.program_code

    def crossover(self, other: 'SRAPLInterpreter') -> str:
        """
        PLACEHOLDER: Krzyżowanie dwóch programów.

        TODO: Implementacja krzyżowania:
        - Wymiana sekcji $PARTS
        - Wymiana bloków kodu
        - Wymiana instrukcji IF

        Args:
            other: Drugi interpreter (rodzic)

        Returns:
            Nowy kod programu (potomek) - obecnie kopia self
        """
        # PLACEHOLDER - do rozwinięcia
        logger.debug("crossover called (PLACEHOLDER)")
        return self.program_code


# --- Aliasy dla kompatybilności wstecznej ---
Interpreter = SRAPLInterpreter


# --- Funkcje pomocnicze ---

def setup_logging(level: int = logging.DEBUG,
                  format_str: str = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'):
    """
    Konfiguruje logowanie dla interpretera SRAPL.

    Args:
        level: Poziom logowania (logging.DEBUG, logging.INFO, etc.)
        format_str: Format komunikatów
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(handler)
    logger.setLevel(level)


# --- Testy i przykłady użycia ---

if __name__ == '__main__':
    # Włącz logowanie debugowe
    setup_logging(logging.DEBUG)

    # Przykładowy program SRAPL
    test_program = '''
$PARTS:
1.0,
2.0,
1.5,
0.5,
0.0,
0.0,
1.0;

$PROGRAMM
# Prosty program testowy
X[0] = 100.0;
X[1] = 5.0;

IF (X[0] - 10.0) {
    # Mamy energię > 10
    IF (5.0 - X[1]) {
        # Przeszkoda blisko -> skanuj
        f_2(1.0, 1.0);
    }
    # Ruch naprzód
    f_1(0.0, 1.0);
}

# Mało energii -> odpoczynek
f_0();
'''

    print("=== Test parsowania ===")
    scales = SRAPLInterpreter.parse_parts_specs(test_program)
    print(f"Parts scales: {scales}")

    print("\n=== Test interpretera (mock automaton) ===")

    # Mock automaton dla testu
    class MockAutomaton:
        def __init__(self):
            self.memory = [0.0] * 64
            self.position = (5, 5)

    mock = MockAutomaton()
    interpreter = SRAPLInterpreter(test_program, debug=True)

    # Wykonaj kilka kroków
    for i in range(5):
        print(f"\n--- Step {i+1} ---")
        func_id, args = interpreter.run_step(mock)
        print(f"Result: {func_id}, args={args}")
        print(f"Memory X[0]={mock.memory[0]}, X[1]={mock.memory[1]}")

    print("\n=== Test zapisu/odczytu pliku ===")
    test_file = '/tmp/test_program.srl'
    interpreter.to_file(test_file)
    loaded = SRAPLInterpreter.from_file(test_file, debug=True)
    print(f"Loaded program length: {len(loaded.program)} chars")

    print("\n=== Test placeholderów mutacji ===")
    mutated = interpreter.mutate_program(0.1)
    print(f"Mutated program length: {len(mutated)} chars")
